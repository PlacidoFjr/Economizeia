"""Third-party expense tracking, backed by the existing financial plan records."""
from datetime import date
import re
from uuid import UUID
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.services.financial_chat_parser import category, occurrence_count, norm
from app.services.financial_chat_service import FinancialPlanItem, lock_user, user_today
from app.services.financial_plan_editor import version_of, lock_item

CARD_ACCOUNT = "Cartão do pai"
LIMIT_KEY = "third_party_card_limits"


class ThirdPartyEntry(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    request_id: UUID
    name: str = Field(min_length=1, max_length=180)
    amount_cents: int = Field(gt=0, le=10_000_000_000, strict=True)
    day: date
    father_card: bool = True
    payer_name: str | None = Field(default=None, max_length=100)
    category: str | None = Field(default=None, min_length=1, max_length=50)


class ThirdPartyLimit(BaseModel):
    amount_cents: int | None = Field(default=None, ge=0, le=10_000_000_000, strict=True)


class ThirdPartyFunding(BaseModel):
    version: str = Field(pattern=r"^[a-f0-9]{64}$")
    father_card: bool


def valid_month(month):
    if not re.fullmatch(r"20\d{2}-(0[1-9]|1[0-2])", month):
        raise HTTPException(422, "Informe o mês no formato AAAA-MM.")
    return month


def on_father_card(item):
    return norm(item.get("account") or "").strip() in {"cartao do pai", "cartao do meu pai"}


def third_amount(item):
    if item.get("kind") != "expense":
        return 0
    if item.get("payer") == "third":
        return item["amount_cents"]
    if item.get("payer") == "shared":
        return max(0, item["amount_cents"] - (item.get("personal_cents") or 0))
    return 0


def third_party_overview(db, user, month):
    valid_month(month)
    rows = db.query(FinancialPlanItem).filter_by(user_id=user.id).all()
    items = []
    for row in rows:
        item = row.data
        amount = third_amount(item)
        if not amount:
            continue
        count = occurrence_count(item, month)
        if not count:
            continue
        items.append({
            "id": str(row.id), "version": version_of(row), "name": item["name"],
            "amount_cents": amount, "total_cents": amount * count,
            "category": item.get("category") or "outras", "frequency": item["frequency"],
            "month": item["month"], "day": item.get("day"),
            "payer_name": item.get("payer_name"), "account": item.get("account"),
            "father_card": on_father_card(item),
            "editable": item["payer"] == "third" and not item.get("shared"),
        })
    actual = [item for item in items if item["frequency"] == "actual"]
    planned = [item for item in items if item["frequency"] != "actual"]
    items.sort(key=lambda item: (item["frequency"] != "actual", item.get("day") or "", item["name"]), reverse=False)
    actual.sort(key=lambda item: (item.get("day") or "", item["name"]), reverse=True)
    limits = (user.notif_prefs or {}).get(LIMIT_KEY) or {}
    limit = limits.get(month)
    spent = sum(item["total_cents"] for item in actual if item["father_card"])
    categories = {}
    for item in actual:
        if item["father_card"]:
            cat = item["category"]
            categories[cat] = categories.get(cat, 0) + item["total_cents"]
    return {
        "month": month, "limit_cents": limit,
        "card_spent_cents": spent,
        "card_remaining_cents": None if limit is None else limit - spent,
        "card_planned_cents": sum(i["total_cents"] for i in planned if i["father_card"]),
        "actual_cents": sum(i["total_cents"] for i in actual),
        "planned_cents": sum(i["total_cents"] for i in planned),
        "card_categories": categories,
        "actual": actual, "planned": planned,
    }


def set_card_limit(db, user, month, entry):
    valid_month(month)
    user = lock_user(db, user.id)
    prefs = dict(user.notif_prefs or {})
    limits = dict(prefs.get(LIMIT_KEY) or {})
    if entry.amount_cents is None:
        limits.pop(month, None)
    else:
        limits[month] = entry.amount_cents
    prefs[LIMIT_KEY] = limits
    user.notif_prefs = prefs
    db.commit()
    return third_party_overview(db, user, month)


def add_third_party_entry(db, user, entry):
    user = lock_user(db, user.id)
    if entry.day > user_today(user):
        raise HTTPException(422, "Informe a data de uma compra já realizada.")
    if entry.day.year < 2000:
        raise HTTPException(422, "Informe uma data a partir de 2000.")
    if not entry.father_card and not entry.payer_name:
        raise HTTPException(422, "Informe quem pagou a despesa.")
    item = {
        "name": entry.name, "amount_cents": entry.amount_cents, "kind": "expense",
        "payer": "third", "payer_name": "Pai" if entry.father_card else entry.payer_name,
        "frequency": "actual", "month": entry.day.strftime("%Y-%m"), "day": entry.day.isoformat(),
        "category": entry.category or category(entry.name, "expense"),
        "account": CARD_ACCOUNT if entry.father_card else None,
        "months": None,
    }
    existing = db.get(FinancialPlanItem, entry.request_id)
    if existing:
        if existing.user_id != user.id or existing.data != item:
            raise HTTPException(409, "Este lançamento já foi processado. Atualize a página.")
    else:
        db.add(FinancialPlanItem(id=entry.request_id, user_id=user.id, data=item))
    db.commit()
    return third_party_overview(db, user, item["month"])


def set_funding(db, user, item_id, entry):
    row = lock_item(db, user.id, item_id, entry.version)
    if row.data.get("kind") != "expense" or row.data.get("payer") != "third" or row.data.get("shared"):
        raise HTTPException(422, "Selecione uma despesa exclusivamente de terceiros.")
    data = dict(row.data)
    if entry.father_card:
        data.update(account=CARD_ACCOUNT, payer_name="Pai")
    elif on_father_card(data):
        data["account"] = None
    row.data = data
    db.commit()
    return {"id": str(row.id), "version": version_of(row)}
