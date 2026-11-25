from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from dataclasses import asdict
from zoneinfo import ZoneInfo
import re
import uuid

from fastapi import HTTPException
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.db.database import Base
from app.db.models import Bill, BillStatus, BillType, User
from app.services.financial_chat_parser import interpret, norm, brl, item_key, get_month, plan_totals, occurs, month_add

# Separate plans from cash movements so another person's expense cannot distort
# the existing dashboard or personal account balance. New tables are additive.
class FinancialChatState(Base):
    __tablename__ = "financial_chat_state"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    draft = Column(JSONB, nullable=False, default=list)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_month = Column(String(7), nullable=True)


class FinancialPlanItem(Base):
    __tablename__ = "financial_plan_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


def reply(text, action="chat", bill_id=None):
    return {"response": text, "action": action, "bill_id": bill_id}


def today_local():
    return datetime.now(ZoneInfo("America/Bahia")).date()


def money_cents(amount):
    return int((Decimal(str(amount or 0)) * 100).quantize(Decimal("1")))


def kind_label(kind):
    return {"income": "Receita", "expense": "Despesa", "budget": "Limite de orçamento", "reserve": "Meta de reserva"}[kind]


def describe(item):
    frequency = item["frequency"]
    when = ("mensal, a partir de " + item["month"]) if frequency == "monthly" else (item.get("day") or item["month"])
    if item.get("months"):
        when += f', por {item["months"]} meses'
    payer = "terceiros" if item["payer"] == "third" else "você"
    status = "realizado" if frequency == "actual" else "previsto"
    account = f' · conta informada: {item["account"]}' if item.get("account") else ""
    return f'• {kind_label(item["kind"])}: {item["name"]} — {brl(item["amount_cents"])} · {status} · {payer} · {when}{account}'


def actual_key(bill):
    return (norm(bill.issuer or "").strip(), money_cents(bill.amount),
            "income" if bill.type == BillType.INCOME else "expense",
            "self", "actual", bill.due_date.strftime("%Y-%m") if bill.due_date else "",
            bill.due_date.isoformat() if bill.due_date else None, None)


def read_bills(db, uid):
    return db.query(Bill).filter(Bill.user_id == uid, Bill.status != BillStatus.CANCELLED).all()


def read_plans(db, uid):
    return [r.data for r in db.query(FinancialPlanItem).filter(FinancialPlanItem.user_id == uid).all()]


def summarize(db, uid, month, query, today):
    bills = read_bills(db, uid)
    plans = read_plans(db, uid)
    monthly = [b for b in bills if b.due_date and b.due_date.strftime("%Y-%m") == month]
    expenses = sum(money_cents(b.amount) for b in monthly if b.type == BillType.EXPENSE and b.status == BillStatus.PAID)
    income = sum(money_cents(b.amount) for b in monthly if b.type == BillType.INCOME and b.status == BillStatus.PAID)
    pending = [b for b in monthly if b.type == BillType.EXPENSE and b.status != BillStatus.PAID]
    pending_total = sum(money_cents(b.amount) for b in pending)
    p = plan_totals(plans, month)
    n = norm(query)
    if any(w in n for w in ("pendente", "em aberto", "falta pagar", "vencid", "vencimento", "vence")):
        # Keep actual unpaid bills separate from planned amounts without a due day.
        selected = pending
        if "vencid" in n or "atrasad" in n:
            selected = [b for b in selected if b.due_date < today]
        elif "amanha" in n:
            selected = [b for b in selected if b.due_date == today + timedelta(days=1)]
        elif "hoje" in n:
            selected = [b for b in selected if b.due_date == today]
        selected.sort(key=lambda b: b.due_date)
        total = sum(money_cents(b.amount) for b in selected)
        text = [f"Contas em aberto ({month}): {len(selected)} — {brl(total)}."]
        text += [f"• {b.issuer or 'Sem descrição'}: {brl(money_cents(b.amount))} — {b.due_date:%d/%m/%Y}" for b in selected[:25]]
        if len(selected) > 25:
            text.append("Mostrando as primeiras 25.")
        text.append(f"Despesas planejadas separadamente: {brl(p['expense'])}. Não são pagamentos efetuados.")
        return "\n".join(text)
    if "categoria" in n or "maiores gastos" in n:
        cats = {}
        for b in monthly:
            if b.type == BillType.EXPENSE and b.status == BillStatus.PAID:
                cat = b.category or "outras"
                cats[cat] = cats.get(cat, 0) + money_cents(b.amount)
        return f"Gastos próprios pagos em {month}:\n" + ("\n".join(f"• {cat}: {brl(v)}" for cat, v in sorted(cats.items(), key=lambda kv: -kv[1])) or "Nenhuma despesa paga registrada.")
    text = [
        f"Resumo financeiro de {month}",
        "",
        "Realizado (lançamentos pagos/recebidos)",
        f"• Receitas próprias: {brl(income)}",
        f"• Despesas próprias: {brl(expenses)}",
        f"• Despesas pagas por terceiros: {brl(p['third_actual'])}",
        f"• Resultado próprio registrado: {brl(income-expenses)}",
        f"• Contas próprias em aberto: {brl(pending_total)}",
        "",
        "Planejamento (não representa saldo bancário)",
        f"• Renda prevista: {brl(p['income'])}",
        f"• Despesas próprias previstas: {brl(p['expense'])}",
        f"• Despesas de terceiros previstas: {brl(p['third'])}",
        f"• Limites de orçamento: {brl(p['budget'])}",
        f"• Meta de reserva: {brl(p['reserve'])}",
        f"• Custo de vida previsto, incluindo terceiros e limites: {brl(p['expense'] + p['third'] + p['budget'])}",
        f"• Renda prevista ainda não alocada: {brl(p['income']-p['expense']-p['budget']-p['reserve'])}",
    ]
    active = [i for i in plans if occurs(i, month) and i["frequency"] != "actual"]
    if active:
        text += ["", "Itens do planejamento:"] + [describe(i) for i in active[:30]]
        if len(active) > 30:
            text.append(f"Mostrando 30 de {len(active)} itens.")
    text.append("Valores previstos e realizados são apresentados separadamente; não são somados entre si.")
    return "\n".join(text)


def handle_financial_chat(message, current_user, db):
    today = today_local()
    now = datetime.now(timezone.utc)
    n = norm(message).strip().strip(".!")
    # Serialize confirmation and duplicate detection per authenticated account.
    user = db.query(User).filter(User.id == current_user.id).with_for_update().one()
    uid = user.id
    # Preserve existing plan quotas; finishing or cancelling a pending draft
    # is free so a user is never prevented from discarding a draft.
    controls = {"cancelar", "cancela", "nao", "descartar", "cancelar lancamentos", "limpar rascunho",
                "sim", "confirmar", "confirmo", "confirmar lancamentos", "pode salvar", "salvar",
                "pode cadastrar", "pode registrar", "sim pode salvar"}
    if n not in controls:
        prefs = dict(user.notif_prefs or {})
        current_month = today.replace(day=1).isoformat()
        count = int(prefs.get("chatbot_messages_this_month") or 0) if str(prefs.get("chatbot_month_reset_date") or "")[:7] == current_month[:7] else 0
        limit = 1000 if prefs.get("is_premium") else 25
        if count >= limit:
            raise HTTPException(status_code=429, detail=f"Limite mensal de {limit} mensagens atingido. Você ainda pode confirmar ou cancelar um rascunho existente.")
        prefs.update(chatbot_messages_this_month=count + 1, chatbot_month_reset_date=current_month)
        user.notif_prefs = prefs
    state = db.query(FinancialChatState).filter_by(user_id=uid).first()
    if state is None:
        state = FinancialChatState(user_id=uid, draft=[])
        db.add(state)
    pending = state.draft or []
    if state.expires_at and state.expires_at <= now:
        state.draft, state.expires_at = [], None
        pending = []
    if n in {"cancelar", "cancela", "nao", "descartar", "cancelar lancamentos", "limpar rascunho"}:
        state.draft, state.expires_at = [], None
        db.commit()
        return reply("Rascunho descartado. Nenhum lançamento salvo.", "cancelled")
    if n in {"sim", "confirmar", "confirmo", "confirmar lancamentos", "pode salvar", "salvar", "pode cadastrar", "pode registrar", "sim pode salvar"}:
        if not pending:
            db.commit()
            return reply("Não existe rascunho pendente. Envie os gastos que deseja cadastrar.")
        bills = read_bills(db, uid)
        plans = read_plans(db, uid)
        keys = {item_key(i) for i in plans}
        keys.update(actual_key(b) for b in bills if b.status == BillStatus.PAID)
        created, skipped, bill_ids = [], [], []
        for item in pending:
            key = item_key(item)
            if key in keys:
                skipped.append(item)
                continue
            keys.add(key)
            if item["frequency"] == "actual" and item["payer"] == "self":
                bill = Bill(id=uuid.uuid4(), user_id=uid, issuer=item["name"],
                            amount=float(Decimal(item["amount_cents"]) / 100),
                            currency="BRL", due_date=date.fromisoformat(item["day"]),
                            type=BillType.INCOME if item["kind"] == "income" else BillType.EXPENSE,
                            status=BillStatus.PAID, is_bill=False, category=item["category"])
                db.add(bill)
                bill_ids.append(str(bill.id))
            else:
                db.add(FinancialPlanItem(user_id=uid, data=item))
            created.append(item)
        state.draft, state.expires_at = [], None
        db.commit()
        lines = [f"Salvei {len(created)} item(ns)."]
        lines += [describe(i) for i in created]
        if skipped:
            lines.append(f"{len(skipped)} item(ns) idêntico(s) já existente(s) foram ignorados.")
        if any(i["frequency"] != "actual" or i["payer"] == "third" for i in created):
            lines.append("Planejamento e gastos de terceiros ficam no resumo do chat, sem alterar seu saldo próprio no dashboard.")
        return reply("\n".join(lines), "transactions_created" if created else "chat", bill_ids[0] if bill_ids else None)
    # Questions must not be mistaken for commands, even if a number is present.
    is_question = bool(re.match(r"^(quanto|quais|qual|como|quando|mostr[ae]|listar|resumo|me (?:mostre|diga)|e (?:no|em|mes)|saldo|gastos por categoria|contas pendentes|planejamento mensal|meu planejamento|meu custo de vida)\b", n)) or ("?" in message and "\n" not in message)
    if is_question:
        if any(w in n for w in ("gasto", "despesa", "receita", "saldo", "planejamento", "custo", "reserva", "orcamento", "pendente", "venc", "mes", "conta", "categoria", "economiz", "recebi", "pagar", "resumo")):
            month = get_month(message, today)
            if n in {"e no mes passado", "e mes passado", "e no mes anterior"} and state.last_month:
                month = month_add(state.last_month, -1)
            state.last_month = month
            response = summarize(db, uid, month, message, today)
            db.commit()
            return reply(response, "financial_summary")
        db.commit()
        return reply("Posso consultar seu saldo registrado, planejamento mensal, categorias, contas pendentes e despesas de terceiros.")
    if n in {"oi", "ola", "bom dia", "boa tarde", "boa noite", "ajuda", "o que voce faz", "o que vc faz"}:
        db.commit()
        return reply("Olá! Envie uma lista de gastos (um por linha), diga quem paga e se é previsto ou já pago. Eu monto um rascunho para você confirmar. Também posso mostrar seu planejamento, saldo registrado e gastos por categoria.")
    items, issues = interpret(message, today)
    if pending:
        # Never append a correction blindly or interpret old chat history as consent.
        db.commit()
        return reply("Há um rascunho aguardando confirmação. Para evitar duplicidades, envie 'confirmar lançamentos' ou 'cancelar'. Para corrigir, cancele e envie a lista corrigida.\n\n" + "\n".join(describe(i) for i in pending), "confirm_transactions")
    if issues:
        db.commit()
        return reply("Ainda não salvei nada. Preciso que ajuste estas informações:\n" + "\n".join("• " + i for i in issues[:15]) + "\nReenvie a lista completa corrigida, com um valor por linha e indicação de mês ou data.", "ask_for_info")
    if not items:
        db.commit()
        return reply("Não consegui identificar um lançamento com segurança. Exemplos: 'Gastei R$ 35 no Uber hoje', 'Academia: R$ 150 por mês, paga pelo meu pai', 'Reserva: R$ 400 por mês'. Você também pode perguntar 'Quanto gastei este mês?'.")
    if len(items) > 60:
        db.commit()
        return reply("Envie até 60 itens por vez. Nenhum lançamento foi salvo.", "ask_for_info")
    state.draft = [asdict(i) for i in items]
    state.expires_at = now + timedelta(minutes=30)
    db.commit()
    return reply(f"Preparei {len(items)} item(ns). Ainda não salvei nenhum lançamento.\n\n" + "\n".join(describe(i) for i in items) + "\n\nConfira valores, tipo, responsável e período. Responda 'confirmar lançamentos' para salvar ou 'cancelar' para descartar.", "confirm_transactions")
