from celery import shared_task  # type: ignore
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Bill, BillDocument, BillStatus
from app.services.ocr_service import ocr_service
from app.services.ollama_service import ollama_service
from app.services.storage_service import storage_service
import logging
from datetime import datetime
from uuid import UUID

logger = logging.getLogger(__name__)


@shared_task
def process_bill_upload(bill_id: str, document_id: str):
    """
    Process bill upload: OCR -> Ollama extraction -> Update bill.
    """
    db: Session = SessionLocal()
    
    try:
        bill = db.query(Bill).filter(Bill.id == UUID(bill_id)).first()
        document = db.query(BillDocument).filter(BillDocument.id == UUID(document_id)).first()
        
        if not bill or not document:
            logger.error(f"Bill or document not found: {bill_id}, {document_id}")
            return
        
        # Download file from storage
        object_name = document.s3_path.split("/", 1)[1] if "/" in document.s3_path else document.s3_path
        file_bytes = storage_service.get_file(object_name)
        
        # Determine content type from file extension or document metadata
        content_type = "application/pdf"  # Default
        if document.s3_path:
            if document.s3_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                content_type = "image/jpeg"  # Default to jpeg for images
            elif document.s3_path.lower().endswith('.pdf'):
                content_type = "application/pdf"
        
        # Perform OCR
        logger.info(f"Starting OCR for bill {bill_id}")
        ocr_text, ocr_confidence = ocr_service.extract_text(file_bytes, content_type)
        document.ocr_text = ocr_text
        document.ocr_confidence = ocr_confidence
        
        # Get presigned URL for image (if needed by Ollama)
        image_url = storage_service.get_presigned_url(object_name, expires_seconds=3600)
        
        # Extrair campos: primeiro regex (rápido), depois AI se necessário
        logger.info(f"Starting field extraction for bill {bill_id}")
        
        # PRIMEIRO: Tentar extração com regex específico para boletos brasileiros
        from app.services.bill_extractor import brazilian_bill_extractor
        regex_extracted = brazilian_bill_extractor.extract_fields(ocr_text)
        
        # Se regex extraiu com boa confiança, usar diretamente
        if regex_extracted.get("confidence", 0.0) >= 0.80:
            logger.info(f"Extraction via regex bem-sucedida (confiança: {regex_extracted['confidence']:.2f})")
            extracted = regex_extracted
        else:
            # Se regex não foi suficiente, usar AI como fallback
            logger.info(f"Regex extraiu com confiança baixa ({regex_extracted.get('confidence', 0):.2f}), tentando AI...")
            import asyncio
            from app.services.gemini_service import get_gemini_service
            
            try:
                ai_service = ollama_service
                logger.info(f"Usando Ollama para extração de campos do boleto {bill_id}")
            except:
                gemini_service = get_gemini_service()
                if gemini_service:
                    ai_service = gemini_service
                    logger.info(f"Ollama não disponível, usando Gemini para extração de campos do boleto {bill_id}")
                else:
                    logger.warning(f"Nenhum serviço de IA disponível, usando resultado do regex")
                    extracted = regex_extracted
                    ai_service = None
            
            if ai_service:
                ai_extracted = asyncio.run(
                    ai_service.extract_bill_fields(
                        ocr_text=ocr_text,
                        image_url=image_url,
                        metadata={"filename": document.s3_path}
                    )
                )
                
                # Combinar resultados: preferir regex para campos essenciais
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
        
        # Categorize with Ollama
        if bill.issuer and bill.amount:
            categorization = asyncio.run(
                ollama_service.categorize_and_detect_anomaly(
                    description=bill.issuer,
                    amount=bill.amount,
                    user_profile={}  # Could load user profile
                )
            )
            if categorization.get("category"):
                bill.category = categorization["category"]
        
        # Set status based on confidence
        if bill.confidence >= 0.9:
            bill.status = BillStatus.CONFIRMED
        else:
            bill.status = BillStatus.PENDING  # Requires manual review
        
        db.commit()
        logger.info(f"Successfully processed bill {bill_id} with confidence {bill.confidence}")
        
    except Exception as e:
        logger.error(f"Error processing bill {bill_id}: {e}", exc_info=True)
        db.rollback()
        if bill:
            bill.status = BillStatus.CANCELLED
            db.commit()
    finally:
        db.close()

