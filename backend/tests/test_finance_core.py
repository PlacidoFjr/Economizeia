"""Unit tests for separating financial contexts and source of payment."""
from datetime import date
from types import SimpleNamespace
from app.api.v1.finance import bill_amounts, first_day, month_bounds
from app.db.models import BillStatus, BillType


def record(amount, type_, payer="self", status=BillStatus.PAID):
    return SimpleNamespace(amount=amount, type=type_, paid_by=payer, status=status)


def test_third_party_expenses_do_not_reduce_available_balance():
    totals = bill_amounts([
        record(2000, BillType.INCOME, "business"),
        record(400, BillType.EXPENSE, "self"),
        record(150, BillType.EXPENSE, "family"),
    ])
    assert totals == {
        "income": 2000.0, "expenses": 400.0,
        "third_party_expenses": 150.0, "balance": 1600.0,
    }


def test_unrealized_movements_do_not_count():
    totals = bill_amounts([
        record(2000, BillType.INCOME, status=BillStatus.PENDING),
        record(200, BillType.EXPENSE, status=BillStatus.SCHEDULED),
    ])
    assert totals["income"] == 0
    assert totals["expenses"] == 0


def test_month_boundary_december_to_january():
    assert first_day(date(2026, 12, 25)) == date(2026, 12, 1)
    assert month_bounds(date(2026, 12, 25)) == (date(2026, 12, 1), date(2027, 1, 1))
