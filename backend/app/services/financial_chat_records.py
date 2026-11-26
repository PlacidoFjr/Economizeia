from datetime import date
from decimal import Decimal
import re
from uuid import UUID, uuid4

from fastapi import HTTPException

from app.db.models import Bill, BillStatus, BillType
from app.services.bill_movements import add_manual_bill, is_open, record_payment
from app.services.financial_chat_intents import BILL_ID, Intent
from app.services.financial_chat_parser import (
    brl, cents, get_day, installment_amounts, money_matches, norm, occurrence_count, occurrence_dates,
)
from app.services.savings_goal_records import add_savings_goal


def money_cents(amount):
    return int((Decimal(str(amount or 0)) * 100).quantize(Decimal("1")))


def scoped_bills(db, uid):
    return db.query(Bill).filter(Bill.user_id == uid, Bill.status != BillStatus.CANCELLED)


def bill_snapshot(bill):
    return {
        "status": bill.status.value,
        "due_date": bill.due_date.isoformat() if bill.due_date else None,
        "amount_cents": money_cents(bill.amount),
        "name": bill.issuer or "Sem descrição",
        "updated_at": bill.updated_at.isoformat() if bill.updated_at else None,
    }


def mutation_draft(db, uid, message, intent, today):
    text = norm(message).strip().rstrip(".!?")
    ids = BILL_ID.findall(text)
    try:
        day = get_day(text, today)
    except ValueError:
        return None, "Informe uma data válida."
    amount = None
    if intent == Intent.EDIT:
        split = re.split(r"\s+(?:para|novo valor|novo vencimento)\s+", text, maxsplit=1)
        if len(split) != 2:
            return None, 'Informe a mudança. Exemplo: “Edite Mercado para R$ 45”.'
        text, change = split
        try:
            day = get_day(change, today)
            _, matches = money_matches(change)
            if len(matches) > 1:
                return None, "Informe somente um novo valor."
            if matches:
                amount = cents(matches[0].group(1), 1000 if matches[0].group(2) else 1)
        except ValueError:
            return None, "Informe um valor ou uma data válida."
        if not day and amount is None:
            return None, "Informe o novo valor ou a nova data."
    name = re.sub(
        r"^(?:\w+\s+)(?:(?:a|o|um|uma|lancamento|despesa|boleto|conta|pagamento|de|do|da|como)\s+)*",
        "", text,
    )
    name = re.split(r"\s+(?:como pago|pago|hoje|ontem|amanha|em \d)\b", name)[0].strip(' "\'')
    name = re.sub(r"^de\s+", "", name)
    if len(ids) > 1:
        return None, "Informe o identificador de um único lançamento."
    query = scoped_bills(db, uid)
    if ids:
        candidates = query.filter(Bill.id == UUID(ids[0])).all()
    else:
        candidates = [b for b in query.all() if norm(b.issuer or "").strip() == name]
    if intent == Intent.PAY:
        candidates = [b for b in candidates if b.type == BillType.EXPENSE and is_open(b) and money_cents(b.amount) > 0]
    if len(candidates) != 1:
        if len(candidates) > 1:
            options = "\n".join(f"• {b.issuer}: {brl(money_cents(b.amount))} · {b.due_date} · ID {b.id}" for b in candidates[:5])
            return None, "Encontrei mais de um lançamento. Repita o comando com o ID de um deles.\n" + options
        return None, "Não encontrei um lançamento elegível com esse nome ou ID."
    bill = candidates[0]
    if intent == Intent.PAY and (not day or day > today):
        return None, 'Informe quando pagou. Exemplo: “Paguei Mercado ontem”.'
    return {
        "operation": intent.value,
        "bill_id": str(bill.id),
        "snapshot": bill_snapshot(bill),
        "new_day": day.isoformat() if day else None,
        "new_amount": amount,
    }, None


def matching_name(name, kind):
    normalized = norm(name or "").strip()
    if kind == "income":
        normalized = re.sub(r"\b(?:depositad[oa]|recebid[oa]|creditad[oa])\b", "", normalized)
        normalized = " ".join(normalized.split())
    return normalized


def matching_open_bills(db, uid, item):
    amount = item.get("personal_cents") or item["amount_cents"]
    bill_type = BillType.INCOME if item["kind"] == "income" else BillType.EXPENSE
    return [
        b for b in scoped_bills(db, uid).filter(Bill.type == bill_type).all()
        if is_open(b) and money_cents(b.amount) == amount and matching_name(b.issuer, item["kind"]) == matching_name(item["name"], item["kind"])
        and b.due_date and b.due_date.strftime("%Y-%m") == item["month"]
    ]


def matching_plan_rows(db, uid, item, plan_model):
    rows = db.query(plan_model).filter(plan_model.user_id == uid).all()
    return [
        row for row in rows
        if row.data["payer"] == "self" and row.data["frequency"] != "actual"
        and not row.data.get("materialized") and row.data["kind"] == item["kind"]
        and matching_name(row.data["name"], item["kind"]) == matching_name(item["name"], item["kind"])
        and row.data["amount_cents"] == (item.get("personal_cents") or item["amount_cents"])
        and occurrence_count(row.data, item["month"]) > len(row.data.get("settled", {}).get(item["month"], []))
    ]


def apply_bill_change(db, uid, operation):
    bill = scoped_bills(db, uid).filter(Bill.id == UUID(operation["bill_id"])).with_for_update().first()
    if bill is None or bill_snapshot(bill) != operation["snapshot"]:
        raise HTTPException(status_code=409, detail="O lançamento mudou. Cancele o rascunho e revise os dados.")
    action = operation["operation"]
    day = date.fromisoformat(operation["new_day"]) if operation.get("new_day") else None
    if action == Intent.DELETE:
        db.delete(bill)
    elif action == Intent.PAY:
        record_payment(db, bill, day)
    elif action == Intent.EDIT:
        if day:
            bill.due_date = day
        if operation.get("new_amount") is not None:
            bill.amount = float(Decimal(operation["new_amount"]) / 100)
    return str(bill.id)


def apply_item(db, uid, item, plan_model):
    if item.get("operation"):
        return [apply_bill_change(db, uid, item)]
    day = date.fromisoformat(item["day"]) if item.get("day") else None
    if item.get("goal"):
        add_savings_goal(db, uid, name=item["name"], target_amount=float(Decimal(item["amount_cents"]) / 100), deadline=day)
        return []

    bill_type = BillType.INCOME if item["kind"] == "income" else BillType.EXPENSE
    is_actual = item["frequency"] == "actual"
    personal_amount = item.get("personal_cents") or item["amount_cents"]
    if item["payer"] == "third" or item["kind"] not in ("income", "expense"):
        db.add(plan_model(user_id=uid, data=item))
        return []
    days = [day] if is_actual else occurrence_dates(item)
    if not days:
        db.add(plan_model(user_id=uid, data=item))
        return []
    amounts = installment_amounts(personal_amount, len(days)) if item.get("installments") else [personal_amount] * len(days)
    group_id = uuid4() if item.get("installments") else None
    output = []
    if item["payer"] == "shared":
        third = dict(item, payer="third", amount_cents=item["amount_cents"] - personal_amount, personal_cents=None, shared=True)
        db.add(plan_model(user_id=uid, data=third))
    if item.get("linked_bill"):
        link = item["linked_bill"]
        bill = scoped_bills(db, uid).filter(Bill.id == UUID(link["bill_id"])).with_for_update().first()
        if bill is None or bill_snapshot(bill) != link["snapshot"]:
            raise HTTPException(status_code=409, detail="O compromisso mudou. Cancele o rascunho e confira o lançamento.")
        if bill.type == BillType.EXPENSE:
            record_payment(db, bill, day)
        else:
            bill.status = BillStatus.PAID
            bill.due_date = day
        return [str(bill.id)]
    for due, amount in zip(days, amounts):
        bill = add_manual_bill(
            db, uid, amount=float(Decimal(amount) / 100), due_date=due, issuer=item["name"],
            bill_type=bill_type, status=BillStatus.PAID if is_actual else BillStatus.PENDING,
            category=item["category"], installment_group_id=group_id,
        )
        output.append(str(bill.id))
    if item.get("linked_plan"):
        plan = db.query(plan_model).filter_by(user_id=uid, id=UUID(item["linked_plan"])).with_for_update().first()
        candidates = matching_plan_rows(db, uid, item, plan_model)
        if plan is None or len(candidates) != 1 or candidates[0].id != plan.id:
            raise HTTPException(status_code=409, detail="O planejamento mudou. Cancele o rascunho e revise os dados.")
        existing = plan.data.get("settled", {})
        plan.data = dict(plan.data, settled={**existing, item["month"]: [*existing.get(item["month"], []), *output]})
    if item["frequency"] in ("weekly", "monthly", "yearly"):
        db.add(plan_model(user_id=uid, data=dict(item, materialized=True, generated_bill_ids=output)))
    return output
