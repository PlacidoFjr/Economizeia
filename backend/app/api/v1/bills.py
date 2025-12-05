from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
import uuid
import logging

from app.db.database import get_db
from app.db.models import User, Bill, BillDocument, BillStatus, BillType
from app.api.dependencies import get_current_user
from app.services.ocr_service import ocr_service
from app.services.ollama_service import ollama_service
from app.services.storage_service import storage_service
from app.services.audit_service import audit_service
from app.core.security import mask_cpf_cnpj
from app.celery_app import celery_app
from fastapi import Request

logger = logging.getLogger(__name__)

router = APIRouter()


class BillPreview(BaseModel):
    issuer: Optional[str] = None
    amount: Optional[float] = None
    currency: str = "BRL"
    due_date: Optional[str] = None
    barcode: Optional[str] = None
    confidence: float = 0.0
    requires_manual_review: bool = True


class BillUploadResponse(BaseModel):
    bill_id: str
    preview: BillPreview
    requires_manual_review: bool


class BillConfirmRequest(BaseModel):
    confirm: bool
    corrections: Optional[dict] = None


class BillScheduleRequest(BaseModel):
    scheduled_date: str  # YYYY-MM-DD
    method: str  # PIX, BOLETO, DEBIT, etc
    notify_before_days: List[int] = [7, 3, 1]


class BillCreateRequest(BaseModel):
    issuer: Optional[str] = None
    amount: float
    currency: str = "BRL"
    due_date: str  # YYYY-MM-DD
    category: Optional[str] = None
    barcode: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "confirmed"  # pending, confirmed, scheduled
    type: Optional[str] = "expense"  # expense ou income
    is_bill: Optional[bool] = False  # False para transações manuais (não-boletos)


@router.post("/upload", response_model=BillUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_bill(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Upload a bill document (PDF/IMG) for processing."""
    try:
        # Validate file type
        content_type = file.content_type or ""
        if not (content_type.startswith("image/") or content_type == "application/pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O arquivo deve ser uma imagem ou PDF"
            )
        
        # Validate file size (max 10MB)
        file_bytes = await file.read()
        if len(file_bytes) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O arquivo é muito grande. Tamanho máximo: 10MB"
            )
        
        # Create bill record (upload sempre é boleto)
        # Campos amount e due_date serão preenchidos após OCR e extração
        bill = Bill(
            id=uuid.uuid4(),
            user_id=current_user.id,
            status=BillStatus.PENDING,
            is_bill=True,  # Upload sempre é boleto
            confidence=0.0,
            amount=None,  # Será preenchido após OCR
            due_date=None,  # Será preenchido após OCR
            issuer=None  # Será preenchido após OCR
        )
        db.add(bill)
        db.commit()
        db.refresh(bill)
        
        # Upload to storage
        object_name = f"bills/{current_user.id}/{bill.id}/{file.filename}"
        try:
            s3_path = storage_service.upload_file(file_bytes, object_name, content_type)
        except Exception as storage_error:
            logger.error(f"Erro ao fazer upload para storage: {storage_error}")
            # Continuar mesmo se storage falhar (usa path mock)
            s3_path = f"mock/{object_name}"
        
        # Create document record
        document = BillDocument(
            id=uuid.uuid4(),
            bill_id=bill.id,
            s3_path=s3_path
        )
        db.add(document)
        db.commit()
        
        # Process asynchronously (opcional - não quebra se Celery não estiver rodando)
        celery_available = False
        try:
            from app.tasks.bill_tasks import process_bill_upload
            process_bill_upload.delay(str(bill.id), str(document.id))
            logger.info(f"Tarefa de processamento agendada para boleto {bill.id}")
            celery_available = True
        except Exception as celery_error:
            logger.warning(f"Celery não disponível, processando sincronamente: {celery_error}")
            celery_available = False
        
        # Se Celery não estiver disponível, processar sincronamente
        if not celery_available:
            try:
                logger.info(f"Processando OCR sincronamente para boleto {bill.id}")
                # Processar OCR diretamente
                ocr_text, ocr_confidence = ocr_service.extract_text(file_bytes, content_type)
                document.ocr_text = ocr_text
                document.ocr_confidence = ocr_confidence
                db.commit()
                
                logger.info(f"OCR concluído para boleto {bill.id}. Texto extraído: {len(ocr_text)} caracteres, confiança: {ocr_confidence:.2f}")
                
                # Se houver texto extraído, tentar extrair campos
                if ocr_text and len(ocr_text.strip()) > 10:
                    try:
                        # PRIMEIRO: Tentar extração com regex específico para boletos brasileiros (rápido e preciso)
                        from app.services.bill_extractor import brazilian_bill_extractor
                        regex_extracted = brazilian_bill_extractor.extract_fields(ocr_text)
                        
                        # Se regex extraiu campos essenciais com boa confiança, usar diretamente
                        if regex_extracted.get("confidence", 0.0) >= 0.80:
                            logger.info(f"Extraction via regex bem-sucedida (confiança: {regex_extracted['confidence']:.2f})")
                            extracted = regex_extracted
                        else:
                            # Se regex não foi suficiente, usar AI (Ollama/Gemini) como fallback
                            logger.info(f"Regex extraiu com confiança baixa ({regex_extracted.get('confidence', 0):.2f}), tentando AI...")
                            import asyncio
                            from app.services.ollama_service import ollama_service
                            from app.services.gemini_service import get_gemini_service
                            
                            try:
                                ai_service = ollama_service
                                logger.info(f"Usando Ollama para extração de campos do boleto {bill.id}")
                            except:
                                gemini_service = get_gemini_service()
                                if gemini_service:
                                    ai_service = gemini_service
                                    logger.info(f"Ollama não disponível, usando Gemini para extração de campos do boleto {bill.id}")
                                else:
                                    logger.warning(f"Nenhum serviço de IA disponível, usando resultado do regex")
                                    extracted = regex_extracted
                                    ai_service = None
                            
                            if ai_service:
                                image_url = None
                                try:
                                    object_name_clean = s3_path.split("/", 1)[1] if "/" in s3_path else s3_path
                                    image_url = storage_service.get_presigned_url(object_name_clean, expires_seconds=3600)
                                except:
                                    pass  # URL opcional
                                
                                ai_extracted = asyncio.run(
                                    ai_service.extract_bill_fields(
                                        ocr_text=ocr_text,
                                        image_url=image_url,
                                        metadata={"filename": file.filename}
                                    )
                                )
                                
                                # Combinar resultados: preferir regex para campos essenciais, AI para outros
                                extracted = {
                                    "issuer": regex_extracted.get("issuer") or ai_extracted.get("issuer"),
                                    "amount": regex_extracted.get("amount") or ai_extracted.get("amount"),
                                    "currency": "BRL",
                                    "due_date": regex_extracted.get("due_date") or ai_extracted.get("due_date"),
                                    "barcode": regex_extracted.get("barcode") or ai_extracted.get("barcode"),
                                    "payment_place": None,
                                    "confidence": max(regex_extracted.get("confidence", 0.0), ai_extracted.get("confidence", 0.0)),
                                    "notes": ai_extracted.get("notes", "")
                                }
                            else:
                                extracted = regex_extracted
                        
                        document.extracted_json = extracted
                        
                        # Update bill with extracted data
                        if extracted.get("issuer"):
                            bill.issuer = extracted["issuer"]
                        if extracted.get("amount"):
                            bill.amount = float(extracted["amount"])
                        if extracted.get("due_date"):
                            try:
                                from datetime import datetime
                                bill.due_date = datetime.fromisoformat(extracted["due_date"]).date()
                            except:
                                pass
                        if extracted.get("barcode"):
                            bill.barcode = extracted["barcode"]
                        if extracted.get("currency"):
                            bill.currency = extracted["currency"]
                        
                        # Calcular confiança: usar a do AI se fornecida e > 0, senão calcular baseado nos campos
                        ai_confidence = extracted.get("confidence", 0.0)
                        if ai_confidence > 0:
                            bill.confidence = ai_confidence
                        else:
                            # Calcular confiança baseada nos campos extraídos
                            has_amount = bill.amount is not None and bill.amount > 0
                            has_due_date = bill.due_date is not None
                            has_issuer = bill.issuer is not None and bill.issuer != ""
                            has_barcode = bill.barcode is not None and bill.barcode != ""
                            
                            if has_amount and has_due_date:
                                bill.confidence = 0.85
                                if has_issuer:
                                    bill.confidence += 0.05
                                if has_barcode:
                                    bill.confidence += 0.05
                                bill.confidence = min(bill.confidence, 0.95)
                            elif has_amount or has_due_date:
                                bill.confidence = 0.65 if has_issuer else 0.55
                            elif has_issuer:
                                bill.confidence = 0.45
                            else:
                                bill.confidence = max(ocr_confidence, 0.3)  # Usar OCR confidence como mínimo
                        
                        # Set status based on confidence
                        if bill.confidence >= 0.9:
                            bill.status = BillStatus.CONFIRMED
                        else:
                            bill.status = BillStatus.PENDING
                        
                        db.commit()
                        logger.info(f"Extraction concluída para boleto {bill.id}. Confiança: {bill.confidence:.2f}")
                    except Exception as extraction_error:
                        logger.warning(f"Erro na extração de campos (OCR foi feito): {extraction_error}")
                        # OCR foi feito, mas extração falhou - boleto fica pendente para revisão manual
                else:
                    logger.warning(f"OCR retornou pouco ou nenhum texto para boleto {bill.id}")
                    
            except Exception as sync_error:
                logger.error(f"Erro ao processar OCR sincronamente: {sync_error}", exc_info=True)
                # Não quebra o upload, mas boleto fica pendente
        
        # Audit log
        try:
            audit_service.log_action(
                db=db,
                entity="bill",
                action="create",
                user_id=current_user.id,
                details={"bill_id": str(bill.id), "filename": file.filename},
                request=request
            )
        except Exception as audit_error:
            logger.warning(f"Erro ao criar audit log: {audit_error}")
            # Não quebra o upload se audit falhar
        
        return BillUploadResponse(
            bill_id=str(bill.id),
            preview=BillPreview(confidence=0.0, requires_manual_review=True),
            requires_manual_review=True
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao fazer upload de boleto: {e}", exc_info=True)
        # Rollback se houver erro
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar upload: {str(e)}"
        )


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_bill(
    bill_data: BillCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Create a new bill/expense manually."""
    try:
        # Parse due date
        due_date = datetime.fromisoformat(bill_data.due_date).date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de data inválido. Use YYYY-MM-DD"
        )
    
    # Validate amount
    if bill_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O valor deve ser maior que zero"
        )
    
    # Validate status
    bill_status = BillStatus.CONFIRMED
    if bill_data.status:
        try:
            bill_status = BillStatus(bill_data.status)
        except ValueError:
            bill_status = BillStatus.CONFIRMED
    
    # Validate type
    bill_type = BillType.EXPENSE
    if bill_data.type:
        try:
            bill_type = BillType(bill_data.type)
        except ValueError:
            bill_type = BillType.EXPENSE
    
    # Default issuer based on type
    default_issuer = "Receita Manual" if bill_type == BillType.INCOME else "Despesa Manual"
    
    # Create bill
    bill = Bill(
        id=uuid.uuid4(),
        user_id=current_user.id,
        issuer=bill_data.issuer or default_issuer,
        amount=bill_data.amount,
        currency=bill_data.currency,
        due_date=due_date,
        barcode=bill_data.barcode,
        status=bill_status,
        type=bill_type,
        is_bill=bill_data.is_bill if bill_data.is_bill is not None else False,  # False para transações manuais
        confidence=1.0,  # Manual entry = 100% confidence
        category=bill_data.category
    )
    
    db.add(bill)
    db.commit()
    db.refresh(bill)
    
    # Audit log
    audit_service.log_action(
        db=db,
        entity="bill",
        action="create_manual",
        user_id=current_user.id,
        details={
            "bill_id": str(bill.id),
            "issuer": bill.issuer,
            "amount": bill.amount,
            "type": bill.type.value,
            "category": bill.category
        },
        request=request
    )
    
    return {
        "id": str(bill.id),
        "issuer": bill.issuer,
        "amount": bill.amount,
        "currency": bill.currency,
        "due_date": bill.due_date.isoformat(),
        "status": bill.status.value,
        "type": bill.type.value,
        "category": bill.category,
        "confidence": bill.confidence
    }


@router.get("/{bill_id}")
async def get_bill(
    bill_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get bill details."""
    bill = db.query(Bill).filter(
        and_(Bill.id == bill_id, Bill.user_id == current_user.id)
    ).first()
    
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Boleto não encontrado"
        )
    
    document = db.query(BillDocument).filter(BillDocument.bill_id == bill.id).first()
    
    # Mask sensitive data if configured
    ocr_text = document.ocr_text if document else None
    if ocr_text:
        ocr_text = mask_cpf_cnpj(ocr_text)
    
    # Gerar URL da imagem do boleto (presigned URL)
    image_url = None
    if document and document.s3_path:
        try:
            from app.services.storage_service import storage_service
            # Extrair object_name do s3_path (formato: bucket/object_name)
            object_name = document.s3_path.split("/", 1)[1] if "/" in document.s3_path else document.s3_path
            # Se for mock path, não tentar gerar URL
            if not object_name.startswith("mock/"):
                image_url = storage_service.get_presigned_url(object_name, expires_seconds=3600)
        except Exception as e:
            logger.warning(f"Erro ao gerar URL da imagem do boleto: {e}")
    
    return {
        "id": str(bill.id),
        "issuer": bill.issuer,
        "amount": bill.amount,
        "currency": bill.currency,
        "due_date": bill.due_date.isoformat() if bill.due_date else None,
        "barcode": bill.barcode,
        "status": bill.status.value,
        "type": bill.type.value if bill.type else "expense",
        "confidence": bill.confidence,
        "category": bill.category,
        "ocr_text": ocr_text,
        "extracted_json": document.extracted_json if document else None,
        "image_url": image_url,  # URL da imagem do boleto
        "created_at": bill.created_at.isoformat() if bill.created_at else None
    }


@router.post("/{bill_id}/confirm")
async def confirm_bill(
    bill_id: UUID,
    confirm_data: BillConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Confirm or correct bill data."""
    bill = db.query(Bill).filter(
        and_(Bill.id == bill_id, Bill.user_id == current_user.id)
    ).first()
    
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Boleto não encontrado"
        )
    
    if confirm_data.confirm:
        # Apply corrections if any
        if confirm_data.corrections:
            if "issuer" in confirm_data.corrections:
                bill.issuer = confirm_data.corrections["issuer"]
            if "amount" in confirm_data.corrections:
                bill.amount = float(confirm_data.corrections["amount"])
            if "due_date" in confirm_data.corrections:
                bill.due_date = datetime.fromisoformat(confirm_data.corrections["due_date"]).date()
            if "barcode" in confirm_data.corrections:
                bill.barcode = confirm_data.corrections["barcode"]
        
        bill.status = BillStatus.CONFIRMED
        bill.confidence = 1.0  # Manual confirmation = 100% confidence
    else:
        bill.status = BillStatus.CANCELLED
    
    db.commit()
    
    # Audit log
    audit_service.log_action(
        db=db,
        entity="bill",
        action="confirm" if confirm_data.confirm else "cancel",
        user_id=current_user.id,
        details={"bill_id": str(bill.id), "corrections": confirm_data.corrections},
        request=request
    )
    
    return {"status": "confirmed" if confirm_data.confirm else "cancelled", "bill_id": str(bill.id)}


@router.post("/{bill_id}/schedule")
async def schedule_payment(
    bill_id: UUID,
    schedule_data: BillScheduleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Schedule a payment for a bill."""
    from app.db.models import Payment, PaymentMethod, PaymentStatus
    from datetime import datetime
    
    bill = db.query(Bill).filter(
        and_(Bill.id == bill_id, Bill.user_id == current_user.id)
    ).first()
    
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Boleto não encontrado"
        )
    
    if bill.status != BillStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O boleto deve estar confirmado antes de agendar o pagamento"
        )
    
    # Create payment
    payment = Payment(
        id=uuid.uuid4(),
        bill_id=bill.id,
        user_id=current_user.id,
        scheduled_date=datetime.fromisoformat(schedule_data.scheduled_date).date(),
        method=PaymentMethod(schedule_data.method),
        status=PaymentStatus.SCHEDULED,
        notify_before_days=schedule_data.notify_before_days
    )
    db.add(payment)
    
    bill.status = BillStatus.SCHEDULED
    db.commit()
    
    # Schedule notifications
    from app.services.notification_service import notification_service
    await notification_service.schedule_reminders(
        db=db,
        user=current_user,
        bill_id=bill.id,
        issuer=bill.issuer or "Desconhecido",
        amount=bill.amount,
        due_date=bill.due_date,
        reminder_days=schedule_data.notify_before_days
    )
    
    # Audit log
    audit_service.log_action(
        db=db,
        entity="payment",
        action="schedule",
        user_id=current_user.id,
        details={"bill_id": str(bill.id), "payment_id": str(payment.id)},
        request=request
    )
    
    return {"payment_id": str(payment.id), "status": "scheduled"}


@router.post("/{bill_id}/mark-paid")
async def mark_paid(
    bill_id: UUID,
    executed_date: str = Form(...),  # YYYY-MM-DD
    comprovante: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Mark bill as paid and upload receipt."""
    from app.db.models import Payment, PaymentMethod, PaymentStatus
    from datetime import datetime
    
    bill = db.query(Bill).filter(
        and_(Bill.id == bill_id, Bill.user_id == current_user.id)
    ).first()
    
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Boleto não encontrado"
        )
    
    # Find or create payment
    payment = db.query(Payment).filter(Payment.bill_id == bill.id).first()
    if not payment:
        payment = Payment(
            id=uuid.uuid4(),
            bill_id=bill.id,
            user_id=current_user.id,
            scheduled_date=bill.due_date,
            method=PaymentMethod.PIX,  # Default
            status=PaymentStatus.EXECUTED
        )
        db.add(payment)
    
    payment.executed_date = datetime.fromisoformat(executed_date).date()
    payment.status = PaymentStatus.EXECUTED
    
    # Upload comprovante if provided
    if comprovante:
        file_bytes = await comprovante.read()
        object_name = f"comprovantes/{current_user.id}/{payment.id}/{comprovante.filename}"
        s3_path = storage_service.upload_file(file_bytes, object_name, comprovante.content_type or "application/pdf")
        payment.comprovante_path = s3_path
    
    bill.status = BillStatus.PAID
    db.commit()
    
    # Audit log
    audit_service.log_action(
        db=db,
        entity="payment",
        action="mark_paid",
        user_id=current_user.id,
        details={"bill_id": str(bill.id), "payment_id": str(payment.id)},
        request=request
    )
    
    return {"status": "paid", "payment_id": str(payment.id)}


@router.get("")
async def list_bills(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    status: Optional[str] = None,
    issuer: Optional[str] = None,
    is_bill: Optional[bool] = None,  # Novo filtro: True para boletos, False para finanças
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List bills with filters. Use is_bill=True for boletos, is_bill=False for outras finanças."""
    query = db.query(Bill).filter(Bill.user_id == current_user.id)
    
    if is_bill is not None:
        query = query.filter(Bill.is_bill == is_bill)
    
    if from_date:
        query = query.filter(Bill.due_date >= datetime.fromisoformat(from_date).date())
    if to_date:
        query = query.filter(Bill.due_date <= datetime.fromisoformat(to_date).date())
    if status:
        query = query.filter(Bill.status == BillStatus(status))
    if issuer:
        query = query.filter(Bill.issuer.ilike(f"%{issuer}%"))
    
    bills = query.order_by(Bill.due_date).all()
    
    return [
        {
            "id": str(bill.id),
            "issuer": bill.issuer,
            "amount": bill.amount,
            "due_date": bill.due_date.isoformat() if bill.due_date else None,
            "status": bill.status.value,
            "type": bill.type.value if bill.type else "expense",
            "is_bill": bill.is_bill if hasattr(bill, 'is_bill') else True,  # Retrocompatibilidade
            "category": bill.category,
            "confidence": bill.confidence
        }
        for bill in bills
    ]


@router.delete("/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bill(
    bill_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Delete a bill or financial transaction."""
    bill = db.query(Bill).filter(
        and_(Bill.id == bill_id, Bill.user_id == current_user.id)
    ).first()
    
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item não encontrado"
        )
    
    # Audit log antes de deletar
    audit_service.log_action(
        db=db,
        entity="bill",
        action="delete",
        user_id=current_user.id,
        details={
            "bill_id": str(bill.id),
            "issuer": bill.issuer,
            "amount": bill.amount,
            "is_bill": bill.is_bill if hasattr(bill, 'is_bill') else True
        },
        request=request
    )
    
    db.delete(bill)
    db.commit()
    
    return None

