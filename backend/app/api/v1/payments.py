from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models import User, Payment, Bill, PaymentStatus
from app.api.dependencies import get_current_user
from app.services.audit_service import audit_service
from fastapi import Request

router = APIRouter()


@router.get("")
async def list_payments(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List payments."""
    query = db.query(Payment).filter(Payment.user_id == current_user.id)
    
    if status:
        query = query.filter(Payment.status == PaymentStatus(status))
    
    payments = query.order_by(Payment.scheduled_date.desc()).all()
    
    return [
        {
            "id": str(payment.id),
            "bill_id": str(payment.bill_id),
            "scheduled_date": payment.scheduled_date.isoformat() if payment.scheduled_date else None,
            "executed_date": payment.executed_date.isoformat() if payment.executed_date else None,
            "method": payment.method.value,
            "status": payment.status.value,
            "amount": payment.bill.amount if payment.bill else None
        }
        for payment in payments
    ]


@router.post("/{payment_id}/reconcile")
async def reconcile_payment(
    payment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Reconcile payment with bank statement."""
    payment = db.query(Payment).filter(
        and_(Payment.id == payment_id, Payment.user_id == current_user.id)
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    if not payment.bill:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment has no associated bill"
        )
    
    # Simple reconciliation logic
    # In production, this would match against uploaded statements
    # For PoC, we'll do a basic match by amount and date
    
    bill = payment.bill
    matched = False
    match_confidence = 0.0
    
    # Check if executed_date is close to due_date (within 5 days)
    if payment.executed_date and bill.due_date:
        days_diff = abs((payment.executed_date - bill.due_date).days)
        if days_diff <= 5:
            match_confidence += 0.3
    
    # Amount match (exact)
    # In real scenario, would check against statement lines
    if payment.executed_date:
        match_confidence += 0.7
        matched = match_confidence >= 0.6
    
    # Audit log
    audit_service.log_action(
        db=db,
        entity="payment",
        action="reconcile",
        user_id=current_user.id,
        details={
            "payment_id": str(payment.id),
            "matched": matched,
            "confidence": match_confidence
        },
        request=request
    )
    
    return {
        "payment_id": str(payment.id),
        "matched": matched,
        "match_confidence": match_confidence,
        "message": "Reconciled successfully" if matched else "No matching statement found"
    }

