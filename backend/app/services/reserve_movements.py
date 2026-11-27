"""A guarded reserve is a cash outflow linked to its reserve record."""
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.db.models import Bill, BillStatus, BillType
from app.services.bill_movements import add_manual_bill


def reserve_bill(db, row):
    key = row.data.get("reserve_bill_id")
    return db.query(Bill).filter_by(id=UUID(key), user_id=row.user_id).first() if key else None


def sync_reserve(db, row, item):
    bill = reserve_bill(db, row)
    if item["kind"] != "reserve" or item["frequency"] != "actual":
        if bill:
            db.delete(bill)
        return item
    if bill is None:
        bill = add_manual_bill(
            db, row.user_id, amount=float(Decimal(item["amount_cents"]) / 100),
            due_date=date.fromisoformat(item["day"]), issuer=item["name"],
            bill_type=BillType.EXPENSE, status=BillStatus.PAID, category="reserva",
        )
    else:
        bill.amount = float(Decimal(item["amount_cents"]) / 100)
        bill.due_date = date.fromisoformat(item["day"])
        bill.issuer, bill.category, bill.status = item["name"], "reserva", BillStatus.PAID
    return dict(item, reserve_bill_id=str(bill.id))


def backfill_reserves(db, plan_model):
    """One-time conversion of existing confirmed reserves, in the startup transaction.

    Keep the marker after a bill is removed so subsequent startups never recreate it.
    Row locks serialize simultaneous application workers.
    """
    count = 0
    for row in db.query(plan_model).order_by(plan_model.id).with_for_update().all():
        if (row.data["kind"] == "reserve" and row.data["frequency"] == "actual"
                and not row.data.get("reserve_bill_id")):
            row.data = sync_reserve(db, row, row.data)
            count += 1
    db.commit()
    return count
