from collections import defaultdict
from datetime import timedelta
import re

from app.db.models import BillType, Payment, PaymentStatus, SavingsGoal, SavingsGoalStatus
from app.services.bill_movements import is_open, is_realized
from app.services.financial_chat_intents import Intent
from app.services.financial_chat_parser import (
    CATEGORIES, NAMED_MONTH, brl, cents, due_dates_in_month, get_day, get_month, money_matches,
    month_add, norm, occurrence_count, plan_totals,
)
from app.services.financial_chat_records import money_cents, scoped_bills


def financial_data(db, uid, plan_model):
    bills = scoped_bills(db, uid).all()
    plans = db.query(plan_model).filter(plan_model.user_id == uid).all()
    payments = db.query(Payment).filter(
        Payment.user_id == uid, Payment.status == PaymentStatus.EXECUTED, Payment.executed_date.isnot(None)
    ).order_by(Payment.executed_date).all()
    dates = {payment.bill_id: payment.executed_date for payment in payments}
    goals = db.query(SavingsGoal).filter(
        SavingsGoal.user_id == uid, SavingsGoal.status != SavingsGoalStatus.CANCELLED
    ).all()
    return bills, plans, dates, goals


def in_month(day, month):
    return day is not None and day.strftime("%Y-%m") == month


def actual_in_month(bills, dates, month):
    return [
        bill for bill in bills
        if is_realized(bill) and in_month(dates.get(bill.id, bill.due_date), month)
    ]


def open_in_month(bills, month, kind=BillType.EXPENSE):
    return [
        bill for bill in bills
        if is_open(bill) and bill.type == kind and in_month(bill.due_date, month)
    ]


def total(bills):
    return sum(money_cents(bill.amount) for bill in bills)


def planned_due(items, month):
    rows = []
    for item in items:
        if (item["frequency"] == "actual" or item["payer"] not in ("self", "shared")
                or item["kind"] != "expense" or item.get("materialized")):
            continue
        due_dates = due_dates_in_month(item, month)
        if len(due_dates) != item["occurrence_count"]:
            continue  # A settled recurrence needs an exact occurrence date before listing a projected due day.
        for day in due_dates:
            rows.append({"id": item["id"] + "-" + day.isoformat(), "name": item["name"],
                         "amount_cents": item.get("personal_cents") or item["amount_cents"],
                         "day": day.isoformat(), "type": "expense", "status": "planned", "category": item["category"]})
    return sorted(rows, key=lambda row: row["day"])


def overview_from_data(data, month, today, history=False):
    bills, plans, dates, _ = data
    movements = actual_in_month(bills, dates, month)
    expenses = [bill for bill in movements if bill.type == BillType.EXPENSE]
    income = total(bill for bill in movements if bill.type == BillType.INCOME)
    expense = total(expenses)
    pending = open_in_month(bills, month)
    realized_ids = {str(bill.id) for bill in movements}
    forecast = dict(income=0, expense=0, third=0, budget=0, reserve=0, third_actual=0)
    items = []
    for row in plans:
        item = row.data
        count = occurrence_count(item, month)
        if not count:
            continue
        linked = item.get("settled", {}).get(month, [])
        remaining_count = count - sum(key in realized_ids for key in linked)
        if remaining_count <= 0:
            continue
        if not item.get("materialized"):
            totals = plan_totals([item], month)
            for key, value in totals.items():
                forecast[key] += value // count * remaining_count
        items.append(dict(item, id=str(row.id), occurrence_count=remaining_count))
    forecast["income"] += total(open_in_month(bills, month, BillType.INCOME))
    forecast["expense"] += total(pending)
    result = {
        "month": month,
        "actual": {"income": income, "expense": expense, "third": forecast["third_actual"],
                   "balance": income - expense, "pending": total(pending)},
        "planned": {**forecast, "available": forecast["income"] - forecast["expense"] - forecast["budget"] - forecast["reserve"],
                    "cost_of_living": forecast["expense"] + forecast["third"]},
        "items": items,
    }
    if history:
        categories, issuers = defaultdict(int), defaultdict(int)
        for bill in expenses:
            categories[bill.category or "outras"] += money_cents(bill.amount)
            issuers[bill.issuer or "Sem descrição"] += money_cents(bill.amount)
        trend = []
        for offset in range(-5, 1):
            period = month_add(month, offset)
            period_bills = actual_in_month(bills, dates, period)
            trend.append({"month": period, "income": total(b for b in period_bills if b.type == BillType.INCOME),
                          "expense": total(b for b in period_bills if b.type == BillType.EXPENSE)})
        upcoming = sorted(pending, key=lambda bill: bill.due_date)
        recent = sorted(
            [bill for bill in bills if in_month(dates.get(bill.id, bill.due_date), month)],
            key=lambda bill: dates.get(bill.id, bill.due_date), reverse=True,
        )
        result["activity"] = {
            "categories": dict(categories), "issuers": dict(issuers), "trend": trend,
            "open_count": len(upcoming), "overdue_count": sum(b.due_date < today for b in upcoming),
            "upcoming": [bill_row(b, b.due_date, "overdue" if b.due_date < today else None) for b in upcoming[:5]],
            "planned_due": planned_due(items, month)[:5],
            "recent": [bill_row(b, dates.get(b.id, b.due_date)) for b in recent[:5]],
        }
    return result


def bill_row(bill, day, status=None):
    return {"id": str(bill.id), "name": bill.issuer or "Sem descrição", "amount_cents": money_cents(bill.amount),
            "day": day.isoformat(), "type": bill.type.value, "status": status or bill.status.value, "category": bill.category}


def answer(data, month, query, today, intent):
    n = norm(query)
    overview = overview_from_data(data, month, today)
    actual, planned = overview["actual"], overview["planned"]
    bills, plans, dates, goals = data
    movements = actual_in_month(bills, dates, month)
    if intent == Intent.SIMULATE:
        _, matches = money_matches(n)
        if len(matches) != 1:
            return "Informe um único valor para simular. Exemplo: “Se eu gastar R$ 300, quanto vai sobrar?”"
        try:
            amount = cents(matches[0].group(1), 1000 if matches[0].group(2) else 1)
        except ValueError:
            return "Informe um valor válido para a simulação."
        future = month > today.strftime("%Y-%m")
        basis = planned["available"] if future else actual["balance"]
        label = "disponível planejado" if future else "resultado próprio realizado"
        return f"Simulação de {month}. Uma despesa de {brl(amount)} levaria o {label} de {brl(basis)} para {brl(basis - amount)}."
    if intent == Intent.COMPARE:
        periods = [month]
        period_pattern = r"\b20\d{2}-\d{2}\b|\b(?:mes (?:passado|anterior|que vem)|este mes)\b|" + NAMED_MONTH.pattern
        for match in re.finditer(period_pattern, n):
            period = get_month(match.group(), today)
            if period not in periods:
                periods.append(period)
        if len(periods) == 1:
            periods.append(today.strftime("%Y-%m") if "mes passado" in n and month != today.strftime("%Y-%m") else month_add(month, -1))
        current, previous = sorted(periods[:2], reverse=True)
        kind = "income" if re.search(r"\b(?:receit|receb)", n) else "balance" if "saldo" in n else "expense"
        label = {"income": "Receitas recebidas", "balance": "Resultado realizado", "expense": "Despesas próprias realizadas"}[kind]
        values = [overview_from_data(data, period, today)["actual"][kind] for period in (current, previous)]
        return f"{label}\n• {current}: {brl(values[0])}\n• {previous}: {brl(values[1])}\nDiferença: {brl(values[0] - values[1])}."
    if re.search(r"pendente|em aberto|falta pagar|vencid|vencimento|vence|atrasad", n):
        try:
            day = get_day(n, today)
        except ValueError:
            return "Informe uma data válida para consultar os vencimentos."
        if day:
            month = day.strftime("%Y-%m")
        pending = open_in_month(bills, month)
        pending = [b for b in pending if (day is None or b.due_date == day) and
                   (not re.search(r"vencid|atrasad", n) or b.due_date < today)]
        pending.sort(key=lambda b: b.due_date)
        title = day.strftime("%d/%m/%Y") if day else month
        lines = [f"Contas próprias em aberto em {title}: {len(pending)} · {brl(total(pending))}."]
        lines.extend(f"• {b.issuer or 'Sem descrição'}: {brl(money_cents(b.amount))} · {b.due_date:%d/%m/%Y}" for b in pending[:25])
        if not re.search(r"vencid|atrasad", n):
            plan = overview if overview["month"] == month else overview_from_data(data, month, today)
            projections = [row for row in planned_due(plan["items"], month) if day is None or row["day"] == day.isoformat()]
            if projections:
                lines.append("Compromissos previstos:")
                lines.extend(f"• {row['name']}: {brl(row['amount_cents'])} · {row['day']}" for row in projections[:10])
        return "\n".join(lines)
    category = next((key for key, words in CATEGORIES.items() if re.search(
        r"\b(?:" + "|".join(map(re.escape, words)) + r")\b", n)), None)
    if re.search(r"orcamento|limite|posso gastar com", n):
        limits = [item for item in overview["items"] if item["kind"] == "budget" and (category is None or item["category"] == category)]
        if not limits:
            return f"Nenhum limite de orçamento correspondente em {month}."
        lines = [f"Orçamento planejado de {month}"]
        for item in limits:
            limit = item["amount_cents"] * item["occurrence_count"]
            spent = total(b for b in movements if b.type == BillType.EXPENSE and b.category == item["category"])
            lines.append(f"• {item['name']}: limite de {brl(limit)} · realizado {brl(spent)} · restante {brl(limit - spent)}")
        return "\n".join(lines)
    if re.search(r"terceir|meu pai|minha mae|meu irmao|minha irma", n):
        relation = re.search(r"\b(meu pai|minha mae|meu irmao|minha irma)\b", n)
        items = [row.data for row in plans if row.data["payer"] in ("third", "shared") and
                 (not relation or norm(row.data.get("payer_name") or "") == relation.group())]
        amounts = plan_totals(items, month)
        return f"Despesas de terceiros em {month}\n• Pagas: {brl(amounts['third_actual'])}\n• Previstas: {brl(amounts['third'])}."
    if "categoria" in n or "maiores gastos" in n or (category and re.search(r"gast|despes", n)):
        categories = defaultdict(int)
        for bill in movements:
            if bill.type == BillType.EXPENSE and (not category or bill.category == category):
                categories[bill.category or "outras"] += money_cents(bill.amount)
        return f"Gastos próprios realizados em {month}:\n" + ("\n".join(
            f"• {key.replace('_', ' ').capitalize()}: {brl(value)}" for key, value in sorted(categories.items(), key=lambda pair: -pair[1])
        ) or "Nenhum gasto correspondente.")
    if re.search(r"custo de vida", n):
        return (f"Custo de vida em {month}\n• Realizado, incluindo terceiros: {brl(actual['expense'] + actual['third'])}"
                f"\n• Previsto, incluindo terceiros: {brl(planned['cost_of_living'])}.")
    if re.search(r"\b(?:guardei|economizei|ja (?:guardei|tenho guardado))\b", n):
        saved = sum(money_cents(goal.current_amount) for goal in goals)
        return (f"Total guardado nas metas até agora: {brl(saved)}."
                f"\nReserva planejada para {month}: {brl(planned['reserve'])}."
                "\nAs metas guardam o total acumulado, sem histórico mensal de aportes.")
    if re.search(r"guardar|reserva|economiz", n):
        return f"Reserva planejada para {month}: {brl(planned['reserve'])}."
    if re.search(r"despesas? fixas|recorrent", n):
        items = [item for item in overview["items"] if item["kind"] == "expense" and item["frequency"] in ("weekly", "monthly", "yearly")]
        return f"Despesas recorrentes previstas em {month}:\n" + ("\n".join(f"• {item['name']}: {brl(item['amount_cents'] * item['occurrence_count'])}" for item in items[:25]) or "Nenhuma despesa recorrente no planejamento.")
    if re.search(r"disponivel|quanto vou ter", n):
        return f"Disponível planejado em {month}: {brl(planned['available'])}."
    if re.search(r"quanto (?:gastei|paguei)|total de despesas", n):
        return f"Despesas próprias realizadas em {month}: {brl(actual['expense'])}."
    if re.search(r"quanto (?:recebi|ganhei)|total de receitas", n):
        return f"Receitas recebidas em {month}: {brl(actual['income'])}."
    if "saldo" in n:
        return f"Resultado próprio realizado em {month}: {brl(actual['balance'])}."
    return (
        f"Resumo financeiro de {month}\n\nRealizado\n• Receitas próprias: {brl(actual['income'])}"
        f"\n• Despesas próprias: {brl(actual['expense'])}\n• Despesas pagas por terceiros: {brl(actual['third'])}"
        f"\n• Resultado próprio: {brl(actual['balance'])}\n• Contas próprias em aberto: {brl(actual['pending'])}"
        f"\n\nPlanejamento\n• Receitas previstas: {brl(planned['income'])}\n• Despesas próprias previstas: {brl(planned['expense'])}"
        f"\n• Despesas de terceiros previstas: {brl(planned['third'])}\n• Limites de orçamento: {brl(planned['budget'])}"
        f"\n• Reserva planejada: {brl(planned['reserve'])}\n• Disponível planejado: {brl(planned['available'])}"
    )
