"""Bill write operations shared by the normal routes and the assistant."""
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import Bill, BillStatus, Payment, PaymentStatus


OPEN_STATUSES = (BillStatus.PENDING, BillStatus.SCHEDULED, BillStatus.OVERDUE)


def is_realized(bill):
    return bill.status == BillStatus.PAID or (bill.status == BillStatus.CONFIRMED and bill.is_bill is False)


def is_open(bill):
    return bill.status in OPEN_STATUSES or (bill.status == BillStatus.CONFIRMED and bill.is_bill is True)


def add_manual_bill(db: Session, user_id, *, amount, due_date, issuer, bill_type, status, category,
                    currency="BRL", barcode=None, is_bill=False, installment_group_id=None, notes=None):
    bill = Bill(id=uuid4(), user_id=user_id, amount=amount, due_date=due_date, issuer=issuer,
                type=bill_type, status=status, category=category, currency=currency, barcode=barcode,
                is_bill=is_bill, confidence=1.0, installment_group_id=installment_group_id, notes=notes)
    db.add(bill)
    return bill


def record_payment(db: Session, bill: Bill, executed_date, default_method=None):
    payment = (db.query(Payment)
               .filter(Payment.bill_id == bill.id, Payment.user_id == bill.user_id)
               .order_by(Payment.created_at.desc())
               .with_for_update()
               .first())
    if payment is None:
        payment = Payment(id=uuid4(), bill_id=bill.id, user_id=bill.user_id,
                          scheduled_date=bill.due_date or executed_date, method=default_method)
        db.add(payment)
    payment.executed_date = executed_date
    payment.status = PaymentStatus.EXECUTED
    bill.status = BillStatus.PAID
    return payment
