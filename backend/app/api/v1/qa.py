from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from uuid import UUID

from app.db.database import get_db
from app.db.models import User, Bill, BillStatus
from app.api.dependencies import get_current_user

router = APIRouter()


class QAResolutionRequest(BaseModel):
    resolution: dict  # Corrections to apply


@router.get("/pending")
async def get_pending_qa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get bills with low confidence requiring manual review."""
    bills = db.query(Bill).filter(
        and_(
            Bill.user_id == current_user.id,
            Bill.confidence < 0.9,
            Bill.status == BillStatus.PENDING
        )
    ).order_by(Bill.confidence.asc()).all()
    
    return [
        {
            "id": str(bill.id),
            "issuer": bill.issuer,
            "amount": bill.amount,
            "due_date": bill.due_date.isoformat() if bill.due_date else None,
            "confidence": bill.confidence,
            "status": bill.status.value
        }
        for bill in bills
    ]


@router.post("/{bill_id}/resolve")
async def resolve_qa(
    bill_id: UUID,
    resolution_data: QAResolutionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resolve QA item by applying corrections."""
    bill = db.query(Bill).filter(
        and_(Bill.id == bill_id, Bill.user_id == current_user.id)
    ).first()
    
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )
    
    # Apply corrections
    if "issuer" in resolution_data.resolution:
        bill.issuer = resolution_data.resolution["issuer"]
    if "amount" in resolution_data.resolution:
        bill.amount = float(resolution_data.resolution["amount"])
    if "due_date" in resolution_data.resolution:
        from datetime import datetime
        bill.due_date = datetime.fromisoformat(resolution_data.resolution["due_date"]).date()
    if "barcode" in resolution_data.resolution:
        bill.barcode = resolution_data.resolution["barcode"]
    
    bill.confidence = 1.0  # Manual resolution = 100% confidence
    bill.status = BillStatus.CONFIRMED
    
    db.commit()
    
    return {"status": "resolved", "bill_id": str(bill.id)}

