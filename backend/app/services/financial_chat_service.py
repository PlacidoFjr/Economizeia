from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
import re
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.db.database import Base
from app.db.models import User
from app.services.financial_chat_intents import Intent, classify
from app.services.financial_chat_parser import (
    brl, category, cents, get_day, get_month, installment_amounts, interpret, money_matches,
    month_add, norm, occurrence_dates,
)
from app.services.financial_chat_records import apply_item, bill_snapshot, matching_open_bills, matching_plan_rows, mutation_draft
from app.services.financial_overview import answer, financial_data, overview_from_data
from app.services.financial_spending import references, reference_candidates


class FinancialChatState(Base):
    __tablename__ = "financial_chat_state"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    draft = Column(JSONB, nullable=False, default=list)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_month = Column(String(7), nullable=True)


class FinancialPlanItem(Base):
    __tablename__ = "financial_plan_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinancialChatTurn(Base):
    __tablename__ = "financial_chat_turns"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    request_id = Column(UUID(as_uuid=True), primary_key=True)
    message = Column(String(16000), nullable=False)
    result = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)


def reply(text, action="chat", bill_id=None, draft_id=None):
    return {"response": text, "action": action, "bill_id": bill_id, "draft_id": draft_id}


def today_local():
    return datetime.now(ZoneInfo("America/Bahia")).date()


def user_today(user):
    tz = (user.notif_prefs or {}).get("timezone")
    if isinstance(tz, str):
        try:
            return datetime.now(ZoneInfo(tz)).date()
        except (ZoneInfoNotFoundError, ValueError):
            pass
    return today_local()


def monthly_financial_overview(db, uid, month, today=None):
    return overview_from_data(financial_data(db, uid, FinancialPlanItem), month, today or today_local(), history=True)


def draft_id(state):
    return state.expires_at.astimezone(timezone.utc).isoformat() if state and state.expires_at else None


def describe(item):
    if item.get("operation"):
        labels = {"pay": "Registrar pagamento", "edit": "Editar lançamento", "delete": "Excluir lançamento"}
        snapshot = item["snapshot"]
        changes = []
        if item["new_day"]:
            changes.append(date.fromisoformat(item["new_day"]).strftime("%d/%m/%Y"))
        if item["new_amount"] is not None:
            changes.append(brl(item["new_amount"]))
        suffix = " → " + " · ".join(changes) if changes else ""
        return f'{labels[item["operation"]]}: {snapshot["name"]} · {brl(snapshot["amount_cents"])}{suffix}'
    labels = {"income": "Receita", "expense": "Despesa", "budget": "Limite de orçamento", "reserve": "Reserva planejada"}
    frequency = item["frequency"]
    when = date.fromisoformat(item["day"]).strftime("%d/%m/%Y") if item.get("day") else item["month"]
    interval = {"monthly": "mensal", "weekly": "semanal", "yearly": "anual"}.get(frequency)
    if interval:
        when = f"{interval} a partir de {when}"
        if item.get("months"):
            when += f' por {item["months"]} meses'
        if item.get("until"):
            when += ' até ' + date.fromisoformat(item["until"]).strftime("%d/%m/%Y")
    status = "realizado" if frequency == "actual" else "previsto"
    label = labels[item["kind"]]
    if item.get("goal"):
        label = "Meta financeira"
        when = when if item.get("day") else "sem prazo"
    payer = ""
    if item["payer"] != "self":
        payer = f' · responsável: {item.get("payer_name") or "terceiros"}'
    if item.get("personal_cents") is not None:
        payer += f' · sua parte: {brl(item["personal_cents"])}'
    installments = ""
    if item.get("installments"):
        charges = installment_amounts(item["amount_cents"], item["installments"])
        charge_text = brl(charges[0]) if charges[0] == charges[-1] else f"{brl(charges[-1])} a {brl(charges[0])}"
        installments = f' · {len(charges)} parcelas de {charge_text} · primeiro vencimento'
    linked = " · vinculado ao compromisso existente" if item.get("linked_bill") or item.get("linked_plan") else ""
    account = f' · conta: {item["account"]}' if item.get("account") else ""
    return f'{label}: {item["name"]} · {brl(item["amount_cents"])} · {status}{installments} · {when}{payer}{account}{linked} · categoria: {item["category"]}'


def preview(state):
    items = "\n".join(f"{index}. {describe(item)}" for index, item in enumerate(state.draft, 1))
    for index, item in enumerate(state.draft, 1):
        if item.get("reference_options"):
            names = ", ".join(option["name"] for option in item["reference_options"])
            items += f'\nEscolha a referência do item {index}: {names}. Responda “Vincule item {index} a NOME”.'
    return reply(
        "Confira o rascunho antes de confirmar.\n\n" + items +
        "\n\nVocê pode confirmar, cancelar ou corrigir um item pelo número.",
        "confirm_transactions", draft_id=draft_id(state),
    )


def set_draft(state, draft, now):
    state.draft = draft
    state.expires_at = now + timedelta(minutes=30) if draft else None


def take_quota(user, today):
    prefs = dict(user.notif_prefs or {})
    month = today.strftime("%Y-%m")
    count = int(prefs.get("chatbot_messages_this_month") or 0) if str(prefs.get("chatbot_month_reset_date") or "")[:7] == month else 0
    limit = 1000 if prefs.get("is_premium") else 25
    if count >= limit:
        raise HTTPException(status_code=429, detail=f"Limite mensal de {limit} mensagens atingido. Você ainda pode confirmar ou cancelar o rascunho.")
    prefs.update(chatbot_messages_this_month=count + 1, chatbot_month_reset_date=month + "-01")
    user.notif_prefs = prefs


def lock_user(db, uid):
    return db.query(User).filter(User.id == uid).populate_existing().with_for_update().one()


def get_state(db, uid):
    return db.query(FinancialChatState).filter_by(user_id=uid).first()


def read_history(db, uid):
    turns = (db.query(FinancialChatTurn).filter_by(user_id=uid)
             .order_by(FinancialChatTurn.created_at.desc(), FinancialChatTurn.request_id.desc()).limit(50).all())
    state = get_state(db, uid)
    active = state and state.draft and state.expires_at and state.expires_at > datetime.now(timezone.utc)
    return {
        "turns": [{"id": str(turn.request_id), "message": turn.message, "result": turn.result,
                   "created_at": turn.created_at.isoformat()} for turn in reversed(turns)],
        "draft": (reply(state.draft[0]["prompt"], "ask_for_info", draft_id=draft_id(state))
                  if state.draft[0].get("missing") else preview(state)) if active else None,
    }


def clear_history(db, uid):
    lock_user(db, uid)
    state = get_state(db, uid)
    if state:
        set_draft(state, [], datetime.now(timezone.utc))
        state.last_month = None
    db.query(FinancialChatTurn).filter_by(user_id=uid).delete(synchronize_session=False)
    db.commit()


def bind_existing(db, uid, items):
    result = []
    used = set()
    for item in items:
        if item.get("operation"):
            result.append(item)
            continue
        item = {key: value for key, value in item.items() if key not in ("linked_bill", "linked_plan")}
        if item["frequency"] == "actual" and item["payer"] != "third":
            matches = matching_open_bills(db, uid, item)
            if len(matches) > 1 or matches and matches[0].id in used:
                return None, f'Há mais de um vínculo possível para “{item["name"]}”. Use “Paguei” seguido do ID do compromisso e da data.'
            if matches:
                bill = matches[0]
                used.add(bill.id)
                item["linked_bill"] = {"bill_id": str(bill.id), "snapshot": bill_snapshot(bill)}
            else:
                plans = matching_plan_rows(db, uid, item, FinancialPlanItem)
                if len(plans) == 1 and plans[0].id not in used:
                    used.add(plans[0].id)
                    item["linked_plan"] = str(plans[0].id)
        if item.get("kind") == "expense" and item.get("frequency") == "actual" and item["payer"] != "third":
            options = references(db.query(FinancialPlanItem).filter_by(user_id=uid).all(), item["month"])
            candidates = reference_candidates(item["name"], item["category"], options)
            selected = next((option for option in options if option["id"] == item.get("expense_plan_id")), None)
            if selected:
                item["category"] = selected["category"]
            elif len(candidates) == 1:
                item["expense_plan_id"] = candidates[0]["id"]
                item.pop("reference_options", None)
            elif len(candidates) > 1:
                item["reference_options"] = candidates
        result.append(item)
    return result, None


def correct_draft(message, state, today):
    text = norm(message)
    selected = re.search(r"\bitem\s+(\d+)\b", text)
    if len(state.draft) > 1 and not selected:
        return None, 'Informe o número do item. Exemplo: “Corrija o item 2 para R$ 45”.'
    index = int(selected.group(1)) - 1 if selected else 0
    if not 0 <= index < len(state.draft):
        return None, "Esse número não corresponde a um item do rascunho."
    item = dict(state.draft[index])
    if item.get("operation"):
        return None, "Cancele o rascunho e informe a alteração atualizada para o lançamento existente."
    link = re.match(r"^vincul(?:e|ar)\s+(?:o\s+)?item\s+\d+\s+(?:a|ao|para)\s+(.+)", text)
    if link:
        options = item.get("reference_options", [])
        target = next((option for option in options if norm(option["name"]) == link.group(1).strip()), None)
        if not target:
            return None, "Escolha uma das referências exibidas para o item."
        item["expense_plan_id"] = target["id"]
        item["category"] = target["category"]
        item.pop("reference_options", None)
        revised = list(state.draft)
        revised[index] = item
        return revised, None
    text = re.sub(r"\bitem\s+\d+\b", "", text)
    new_name = re.search(r"\b(?:descrição|descri[cç][aã]o|nome)\s*(?::|para)?\s+(.+)", message, re.I)
    if new_name:
        name = new_name.group(1).strip().strip('."“”')
        if not 2 <= len(name) <= 180 or "\n" in name:
            return None, "Informe uma descrição entre 2 e 180 caracteres."
        item.update(name=name, category=category(name, item["kind"]))
        revised = list(state.draft)
        revised[index] = item
        return revised, None
    try:
        day = get_day(text, today)
        _, amounts = money_matches(text)
        if len(amounts) > 1:
            return None, "Informe um único valor para o item."
        if amounts:
            amount = cents(amounts[0].group(1), 1000 if amounts[0].group(2) else 1)
            if amount < (item.get("installments") or 1) or item.get("personal_cents") and amount <= item["personal_cents"]:
                return None, "O novo valor precisa cobrir todas as parcelas ou ser maior que a sua parte."
            item["amount_cents"] = amount
    except ValueError:
        return None, "Informe um valor ou uma data válida."
    if day:
        if day > today and item["frequency"] == "actual" or item.get("until") and day.isoformat() > item["until"]:
            return None, "A data informada é incompatível com a situação ou o período deste item."
        item.update(day=day.isoformat(), month=day.strftime("%Y-%m"))
    elif re.search(r"\b(?:para|em|pro)\s+(?:" + "|".join((
        "janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
        "o proximo mes", "mes que vem",
    )) + r")\b", text):
        if item["frequency"] in ("actual", "weekly") or item.get("installments") or item.get("until"):
            return None, "Informe a data completa para mudar o período desse item."
        item.update(month=get_month(text, today), day=None)
    elif not amounts:
        return None, "Informe a nova data, o mês ou o valor que deseja corrigir."
    revised = list(state.draft)
    revised[index] = item
    return revised, None


def collect_missing(message, state, today):
    partial = state.draft[0]
    if partial["missing"] == "description":
        description = message.strip().strip(".!?")
        if not 2 <= len(description) <= 150 or "\n" in description or money_matches(norm(description))[1]:
            return None, "Qual é a descrição do lançamento?"
        try:
            known_day = get_day(partial["original"], today)
        except ValueError:
            known_day = None
        if known_day:
            return interpret(description + ": " + partial["original"], today)
        return [{"missing": "date", "original": description + ": " + partial["original"],
                 "prompt": "Em que dia aconteceu? Você pode responder “hoje”, “ontem” ou informar a data."}], []
    try:
        day = get_day(message, today)
    except ValueError:
        day = None
    if not day:
        return None, partial["prompt"]
    return interpret(partial["original"] + " " + day.isoformat(), today)


def contextual_query(db, uid, message, today):
    if not re.match(r"^e (?:no|em|mes)\b", norm(message)):
        return message
    turns = (db.query(FinancialChatTurn).filter_by(user_id=uid)
             .order_by(FinancialChatTurn.created_at.desc()).limit(10).all())
    for turn in turns:
        if classify(turn.message) != Intent.CONSULT or re.match(r"^e (?:no|em|mes)\b", norm(turn.message)):
            continue
        try:
            if not get_day(turn.message, today):
                return turn.message
        except ValueError:
            continue
    return message


def process_message(message, user, state, db, now, expected_draft):
    today = user_today(user)
    intent = classify(message)
    pending = state.draft or []
    if state.expires_at and state.expires_at <= now:
        set_draft(state, [], now)
        pending = []
    if intent in (Intent.CANCEL, Intent.CONFIRM):
        if expected_draft and expected_draft != (draft_id(state) or "none"):
            raise HTTPException(status_code=409, detail="O rascunho mudou. Abra a versão atual antes de decidir.")
        if intent == Intent.CANCEL:
            set_draft(state, [], now)
            return reply("Rascunho descartado.", "cancelled")
        if not pending:
            return reply("Não existe rascunho pendente. Envie o que deseja cadastrar.")
        if pending[0].get("missing"):
            return reply(pending[0]["prompt"], "ask_for_info")
        if any(item.get("reference_options") for item in pending):
            return preview(state)
        ids = [bill_id for item in pending for bill_id in apply_item(db, user.id, item, FinancialPlanItem)]
        db.flush()
        expense_items = [item for item in pending if not item.get("operation") and item.get("kind") == "expense" and item.get("frequency") == "actual"]
        impact = []
        for period in sorted({item["month"] for item in expense_items}):
            overview = monthly_financial_overview(db, user.id, period, today)
            for group in overview["spending"]:
                if group["planned"] is not None and any(item["category"] == group["category"] for item in expense_items):
                    remaining = group["remaining"]
                    suffix = f"Restam {brl(remaining)}" if remaining >= 0 else f"Excesso de {brl(-remaining)}"
                    impact.append(f'{group["category"].capitalize()}: {brl(group["actual"])} de {brl(group["planned"])} previstos em {period}. {suffix}.')
        total_text = f'\nTotal de despesas registradas: {brl(sum(item.get("personal_cents") or item["amount_cents"] for item in expense_items))}.' if expense_items else ""
        set_draft(state, [], now)
        return reply(f"Concluí {len(pending)} operação(ões).\n\n" + "\n".join("• " + describe(item) for item in pending) + total_text + ("\n\n" + "\n".join(impact) if impact else ""),
                     "transactions_created", ids[0] if ids else None)

    take_quota(user, today)
    if intent in (Intent.CONSULT, Intent.SIMULATE, Intent.COMPARE):
        month = get_month(message, today)
        if norm(message).strip(".?! ") in {"e no mes passado", "e mes passado", "e no mes anterior"} and state.last_month:
            month = month_add(state.last_month, -1)
        state.last_month = month
        question = contextual_query(db, user.id, message, today)
        return reply(answer(financial_data(db, user.id, FinancialPlanItem), month, question, today, intent), "financial_summary")
    if intent == Intent.HELP:
        return reply("Posso registrar receitas e despesas, organizar compromissos e consultar seus valores. Envie um item por linha. Vou pedir confirmação antes de alterar seus dados.")
    if pending and pending[0].get("missing"):
        items, issues = collect_missing(message, state, today)
        if items is None:
            return reply(issues, "ask_for_info")
        if items and isinstance(items[0], dict):
            set_draft(state, items, now)
            return reply(items[0]["prompt"], "ask_for_info")
    elif pending:
        if intent != Intent.CORRECT:
            return preview(state)
        items, issue = correct_draft(message, state, today)
        if issue:
            return reply(issue + "\n\n" + preview(state)["response"], "confirm_transactions", draft_id=draft_id(state))
        items, issue = bind_existing(db, user.id, items)
        if issue:
            return reply(issue, "ask_for_info")
        set_draft(state, items, now)
        return preview(state)
    elif intent in (Intent.PAY, Intent.EDIT, Intent.DELETE):
        item, issue = mutation_draft(db, user.id, message, intent, today)
        if issue:
            return reply(issue, "ask_for_info")
        set_draft(state, [item], now)
        return preview(state)
    elif intent == Intent.CORRECT:
        return reply("Abra um rascunho antes de corrigir um item.", "ask_for_info")
    else:
        items, issues = interpret(message, today)
        if not items and len(issues) == 1 and "\n" not in message and "data do primeiro vencimento" in issues[0]:
            try:
                known_day = get_day(message, today)
            except ValueError:
                known_day = None
            if known_day is None and re.search(r"\b\d+\s*(?:x|parcelas|vezes)\b", norm(message)):
                prompt = "Qual é a data do primeiro vencimento?"
                set_draft(state, [{"missing": "date", "original": message, "prompt": prompt}], now)
                return reply(prompt, "ask_for_info")
        if not items and len(issues) == 1 and "(informe a descricao)" in issues[0] and re.match(
            r"^(?:gastei|recebi|ganhei|paguei|comprei)\b", norm(message)
        ) and "\n" not in message:
            prompt = "De onde veio essa receita?" if re.match(r"^(?:recebi|ganhei)\b", norm(message)) else "Com o que foi esse gasto?"
            set_draft(state, [{"missing": "description", "original": message, "prompt": prompt}], now)
            return reply(prompt, "ask_for_info")
    if issues:
        return reply("Confira estes dados antes de continuar:\n" + "\n".join("• " + issue for issue in issues[:15]), "ask_for_info")
    if not items:
        return reply('Envie uma descrição e um valor. Exemplo: “Gastei R$ 35 no Uber ontem”.', "ask_for_info")
    if len(items) > 60 or sum(len(occurrence_dates(asdict(item))) or 1 for item in items) > 750:
        return reply("Divida a lista em lotes menores para revisar e confirmar.", "ask_for_info")
    items, issue = bind_existing(db, user.id, [asdict(item) for item in items])
    if issue:
        return reply(issue, "ask_for_info")
    set_draft(state, items, now)
    return preview(state)


def handle_financial_chat(message, current_user, db, request_id=None, expected_draft=None, entry=None):
    now = datetime.now(timezone.utc)
    uid = current_user.id
    user = lock_user(db, uid)
    if request_id:
        prior = db.get(FinancialChatTurn, (uid, request_id))
        if prior:
            if prior.message != message or (entry is not None and prior.result.get("entry") != entry):
                raise HTTPException(status_code=409, detail="Esta requisição já foi usada para outra mensagem.")
            db.commit()
            return prior.result
    state = get_state(db, uid)
    if state is None:
        state = FinancialChatState(user_id=uid, draft=[])
        db.add(state)
    if entry is not None:
        today = user_today(user)
        if date.fromisoformat(entry["day"]) > today:
            raise HTTPException(422, "Informe a data em que o lançamento aconteceu.")
        name = entry["name"].strip()
        if not name or any(char in name for char in "\n\r"):
            raise HTTPException(422, "Informe uma descrição em uma linha.")
        if state.draft and state.expires_at and state.expires_at > now:
            raise HTTPException(409, "Confirme ou cancele o rascunho pendente antes de adicionar outro lançamento.")
        take_quota(user, today)
        item = {"kind": entry["kind"], "name": name, "amount_cents": entry["amount_cents"],
                "day": entry["day"], "month": entry["day"][:7], "frequency": "actual",
                "payer": "self", "category": category(name, entry["kind"])}
        # An explicit form entry is a separate movement, even when its value matches another.
        set_draft(state, [item], now)
        result = preview(state)
        result["entry"] = entry
    else:
        result = process_message(message, user, state, db, now, expected_draft)
    db.add(FinancialChatTurn(user_id=uid, request_id=request_id or uuid4(), message=message, result=result))
    db.commit()
    return result
