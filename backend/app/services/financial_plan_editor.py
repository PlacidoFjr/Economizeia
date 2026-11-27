from datetime import date
from decimal import Decimal
from hashlib import sha256
import json
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import selectinload

from app.db.models import Bill, BillStatus, BillType
from app.services.bill_movements import add_manual_bill, is_open, is_realized
from app.services.financial_chat_parser import occurrence_dates
from app.services.financial_chat_records import money_cents
from app.services.financial_chat_service import FinancialPlanItem, lock_user
from app.services.reserve_movements import reserve_bill, sync_reserve


class PlanEdit(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    version: str = Field(pattern=r"^[a-f0-9]{64}$")
    name: str = Field(min_length=1, max_length=180)
    amount_cents: int = Field(gt=0, le=10_000_000_000, strict=True)
    kind: Literal["income", "expense", "budget", "reserve"]
    payer: Literal["self", "third", "shared"]
    frequency: Literal["once", "weekly", "monthly", "yearly", "actual"]
    month: str = Field(pattern=r"^20\d{2}-(0[1-9]|1[0-2])$")
    day: date | None = None
    until: date | None = None
    months: int | None = Field(default=None, ge=1, le=120, strict=True)
    category: str = Field(default="outras", min_length=1, max_length=50)
    account: str | None = Field(default=None, max_length=100)
    payer_name: str | None = Field(default=None, max_length=100)
    personal_cents: int | None = Field(default=None, gt=0, strict=True)


def version_of(row):
    return sha256(json.dumps(row.data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def serialize_plan(row):
    fields = set(PlanEdit.model_fields) - {"version"}
    return {key: value for key, value in row.data.items() if key in fields} | {
        "id": str(row.id), "version": version_of(row), "shared": bool(row.data.get("shared")),
    }


def list_items(db, uid):
    rows = db.query(FinancialPlanItem).filter_by(user_id=uid).order_by(FinancialPlanItem.created_at.desc(), FinancialPlanItem.id).all()
    output = []
    for row in rows:
        item = serialize_plan(row)
        if row.data.get("reserve_bill_id"):
            bill = reserve_bill(db, row)
            if bill is None or bill.status == BillStatus.CANCELLED:
                continue
            item.update(amount_cents=money_cents(bill.amount), name=bill.issuer,
                        day=bill.due_date.isoformat(), month=bill.due_date.strftime("%Y-%m"))
        output.append(item)
    return output


def lock_item(db, uid, item_id, version):
    lock_user(db, uid)
    row = db.query(FinancialPlanItem).filter_by(user_id=uid, id=item_id).with_for_update().first()
    if row is None:
        raise HTTPException(404, "Item do planejamento não encontrado.")
    if version_of(row) != version:
        raise HTTPException(409, "O item foi atualizado. Reabra a edição para usar os dados mais recentes.")
    return row


def validate_schedule(edit, today):
    if edit.day and edit.day.strftime("%Y-%m") != edit.month:
        raise HTTPException(422, "A data inicial deve pertencer ao mês informado.")
    if edit.frequency == "weekly" and not edit.day:
        raise HTTPException(422, "Informe a primeira data para uma recorrência semanal.")
    if edit.months is not None and edit.frequency != "monthly":
        raise HTTPException(422, "A quantidade de meses se aplica à frequência mensal.")
    recurring = edit.frequency in ("weekly", "monthly", "yearly")
    if edit.until and (not recurring or edit.months or
                       edit.until < (edit.day or date.fromisoformat(edit.month + "-01")) or
                       (edit.until - (edit.day or date.fromisoformat(edit.month + "-01"))).days > 3660):
        raise HTTPException(422, "Confira a data final da recorrência ou informe a quantidade de meses.")
    if edit.kind != "expense" and edit.payer != "self":
        raise HTTPException(422, "O responsável pelo pagamento se aplica às despesas.")
    if edit.payer == "shared" and (edit.personal_cents is None or edit.personal_cents >= edit.amount_cents):
        raise HTTPException(422, "Informe a sua parte, menor que o valor total.")
    if edit.frequency == "actual" and ((edit.kind, edit.payer) not in (("expense", "third"), ("reserve", "self")) or not edit.day or edit.day > today):
        raise HTTPException(422, "Informe uma reserva guardada ou uma despesa de terceiros e a data em que aconteceu.")
    if edit.payer != "shared" and edit.personal_cents is not None:
        raise HTTPException(422, "A sua parte se aplica às despesas compartilhadas.")


def generated_bills(db, row):
    if not row.data.get("materialized"):
        return []
    query = (db.query(Bill).filter(Bill.user_id == row.user_id)
             .options(selectinload(Bill.payments)).order_by(Bill.id).with_for_update())
    ids = row.data.get("generated_bill_ids")
    if ids is not None:
        return query.filter(Bill.id.in_([UUID(value) for value in ids])).all()

    # PostgreSQL gives rows created in the same transaction the same timestamp.
    item = row.data
    days = set(occurrence_dates(item))
    expected_type = BillType.INCOME if item["kind"] == "income" else BillType.EXPENSE
    amount = item.get("personal_cents") or item["amount_cents"]
    candidates = query.filter(
        Bill.created_at == row.created_at, Bill.issuer == item["name"], Bill.type == expected_type,
        Bill.is_bill.is_(False), Bill.installment_group_id.is_(None)
    ).all()
    matches = [bill for bill in candidates if bill.due_date in days and money_cents(bill.amount) == amount]
    if len(matches) != len(days) or {bill.due_date for bill in matches} != days:
        raise HTTPException(409, "Não foi possível identificar todos os lançamentos dessa série antiga com segurança. Confira os lançamentos em Finanças.")
    return matches


def editable_bill(bill):
    return bill.status in (BillStatus.PENDING, BillStatus.OVERDUE) and not bill.payments


def refresh_generated_bills(db, row, item, today):
    bills = generated_bills(db, row)
    if not row.data.get("materialized"):
        return
    available = {bill.due_date: bill for bill in bills if editable_bill(bill)}
    protected = [bill for bill in bills if not editable_bill(bill)]
    days = occurrence_dates(item) if item["payer"] == "self" and item["kind"] in ("income", "expense") else []
    if any(is_open(bill) for bill in protected) and (
        not days or item["kind"] != row.data["kind"] or
        any(is_open(bill) and bill.due_date not in days for bill in protected)
    ):
        raise HTTPException(409, "Esta série tem um pagamento agendado. Confira o pagamento antes de mudar ou remover a data do compromisso.")

    retained = [str(bill.id) for bill in protected]
    protected_dates = {bill.due_date: bill for bill in protected}
    amount = float(Decimal(item["amount_cents"]) / 100)
    kind = BillType.INCOME if item["kind"] == "income" else BillType.EXPENSE
    for day in days:
        protected_bill = protected_dates.get(day)
        if protected_bill:
            if is_open(protected_bill):
                protected_bill.issuer, protected_bill.amount, protected_bill.category = item["name"], amount, item["category"]
            continue
        if day < today and day not in available:
            continue
        bill = available.pop(day, None)
        if bill:
            bill.issuer, bill.amount, bill.category, bill.type = item["name"], amount, item["category"], kind
        else:
            bill = add_manual_bill(db, row.user_id, amount=amount, due_date=day, issuer=item["name"],
                                   bill_type=kind, status=BillStatus.PENDING, category=item["category"])
        retained.append(str(bill.id))
    for bill in available.values():
        db.delete(bill)
    if days:
        item.update(materialized=True, generated_bill_ids=retained)
    elif item["kind"] == row.data["kind"] and item["payer"] == "self":
        settled = item.setdefault("settled", {})
        for bill in protected:
            if bill.due_date and is_realized(bill):
                period = bill.due_date.strftime("%Y-%m")
                settled[period] = list(dict.fromkeys([*settled.get(period, []), str(bill.id)]))


def update_item(db, uid, item_id, edit, today):
    validate_schedule(edit, today)
    row = lock_item(db, uid, item_id, edit.version)
    item = edit.model_dump(mode="json", exclude={"version"})
    if (item["kind"], item["payer"]) == (row.data["kind"], row.data["payer"]):
        item["settled"] = dict(row.data.get("settled", {}))
        if row.data.get("shared"):
            item["shared"] = True
    refresh_generated_bills(db, row, item, today)
    item = sync_reserve(db, row, item)
    row.data = item
    db.commit()
    return serialize_plan(row)


def delete_item(db, uid, item_id, version):
    row = lock_item(db, uid, item_id, version)
    reserve = reserve_bill(db, row)
    if reserve:
        db.delete(reserve)
    bills = generated_bills(db, row)
    if any(is_open(bill) and not editable_bill(bill) for bill in bills):
        raise HTTPException(409, "Esta série tem um pagamento agendado. Confira o pagamento antes de excluir a série.")
    for bill in bills:
        if editable_bill(bill):
            db.delete(bill)
    db.delete(row)
    db.commit()

