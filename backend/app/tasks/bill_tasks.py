from celery import shared_task
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
        
        # Extract structured data with Ollama
        logger.info(f"Starting Ollama extraction for bill {bill_id}")
        import asyncio
        extracted = asyncio.run(
            ollama_service.extract_bill_fields(
                ocr_text=ocr_text,
                image_url=image_url,
                metadata={"filename": document.s3_path}
            )
        )
        
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
        
        bill.confidence = extracted.get("confidence", 0.0)
        
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

