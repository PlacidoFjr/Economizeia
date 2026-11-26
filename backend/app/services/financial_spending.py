"""Monthly spending references shared by the dashboard and assistant."""
import re

from app.services.financial_chat_parser import category, norm, occurrence_count
from app.services.financial_chat_records import money_cents


def transport_group(name):
    text = norm(name)
    if re.search(r"\b(?:uber|99|moto|taxi)\b", text):
        return "ride"
    if re.search(r"\b(?:onibus|metro|passagem|salvador card)\b", text):
        return "public"
    return None


def references(plans, month):
    output = []
    for row in plans:
        item = row.data
        if (item["kind"] not in ("expense", "budget") or item["frequency"] == "actual"
                or item["payer"] not in ("self", "shared")):
            continue
        count = occurrence_count(item, month)
        if not count:
            continue
        output.append({
            "id": str(row.id), "name": item["name"], "category": item.get("category") or category(item["name"], "expense"),
            "kind": item["kind"], "planned": (item.get("personal_cents") or item["amount_cents"]) * count,
        })
    return output


def reference_candidates(name, cat, options):
    candidates = [item for item in options if item["category"] == cat]
    exact = [item for item in candidates if norm(item["name"]).strip() == norm(name).strip()]
    if exact:
        candidates = exact
    elif cat == "transporte" and transport_group(name):
        group = transport_group(name)
        specific = [item for item in candidates if transport_group(item["name"]) == group]
        generic = [item for item in candidates if transport_group(item["name"]) is None]
        candidates = specific or generic
    # A budget for a category is the spending ceiling, overriding forecasts for that same scope.
    budgets = [item for item in candidates if item["kind"] == "budget"]
    candidates = budgets or candidates
    return candidates


def choose_reference(name, cat, options):
    candidates = reference_candidates(name, cat, options)
    return candidates[0]["id"] if len(candidates) == 1 else None


def spending_overview(plans, expenses, month):
    options = references(plans, month)
    by_id = {item["id"]: item for item in options}
    categories = {}
    for item in options:
        cat = item["category"]
        categories.setdefault(cat, {"category": cat, "planned": None, "actual": 0, "items": [], "transactions": []})
        categories[cat]["items"].append(dict(item, actual=0, transactions=[]))
    for bill in expenses:
        cat = bill.category or category(bill.issuer or "", "expense")
        requested = bill.expense_plan_id
        selected = requested if requested in by_id else choose_reference(bill.issuer or "", cat, options)
        if selected and requested in by_id:
            cat = by_id[selected]["category"]
        group = categories.setdefault(cat, {"category": cat, "planned": None, "actual": 0, "items": [], "transactions": []})
        amount = money_cents(bill.amount)
        transaction = {"id": str(bill.id), "name": bill.issuer or "Sem descrição", "amount_cents": amount,
                       "day": bill.due_date.isoformat() if bill.due_date else None, "category": cat,
                       "plan_id": selected, "needs_link": selected is None and bool(group["items"])}
        group["actual"] += amount
        group["transactions"].append(transaction)
        for item in group["items"]:
            if item["id"] == selected:
                item["actual"] += amount
                item["transactions"].append(transaction)
    for group in categories.values():
        items = group["items"]
        budgets = [item for item in items if item["kind"] == "budget"]
        # Explicit category budget replaces the sum of category forecasts.
        basis = budgets or items
        group["planned"] = sum(item["planned"] for item in basis) if basis else None
        group["basis"] = "budget" if budgets else "forecast"
        for row in [group, *items]:
            expected = row["planned"]
            row["remaining"] = expected - row["actual"] if expected is not None else None
            row["percent"] = round(row["actual"] / expected * 100, 1) if expected else None
    return sorted(categories.values(), key=lambda group: group["category"])

