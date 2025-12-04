from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
import uuid

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
    # Validate file type
    content_type = file.content_type or ""
    if not (content_type.startswith("image/") or content_type == "application/pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo deve ser uma imagem ou PDF"
        )
    
    # Read file
    file_bytes = await file.read()
    
    # Create bill record (upload sempre é boleto)
    bill = Bill(
        id=uuid.uuid4(),
        user_id=current_user.id,
        status=BillStatus.PENDING,
        is_bill=True,  # Upload sempre é boleto
        confidence=0.0
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    
    # Upload to storage
    object_name = f"bills/{current_user.id}/{bill.id}/{file.filename}"
    s3_path = storage_service.upload_file(file_bytes, object_name, content_type)
    
    # Create document record
    document = BillDocument(
        id=uuid.uuid4(),
        bill_id=bill.id,
        s3_path=s3_path
    )
    db.add(document)
    db.commit()
    
    # Process asynchronously
    from app.tasks.bill_tasks import process_bill_upload
    process_bill_upload.delay(str(bill.id), str(document.id))
    
    # Audit log
    audit_service.log_action(
        db=db,
        entity="bill",
        action="create",
        user_id=current_user.id,
        details={"bill_id": str(bill.id), "filename": file.filename},
        request=request
    )
    
    return BillUploadResponse(
        bill_id=str(bill.id),
        preview=BillPreview(confidence=0.0, requires_manual_review=True),
        requires_manual_review=True
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

