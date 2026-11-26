"""Deterministic, conservative Portuguese financial chat interpretation.

No model output or browser-provided history can authorize a write.
Amounts are parsed as integer BRL cents. Ambiguous input is not committed.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import re
import unicodedata
from calendar import monthrange

MONTHS = ("janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro").split()
NAMED_MONTH = re.compile(r"\b(" + "|".join(MONTHS) + r")(?:\s+(?:de\s+)?(20\d{2}))?\b")
LONG_DATE = re.compile(r"\b(?:dia\s+)?(\d{1,2})\s+de\s+(" + "|".join(MONTHS) + r")(?:\s+de\s+(20\d{2}))?\b")
MONEY = re.compile(r"(?<![\d.,])(?:r\$\s*)?(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:[,.]\d{1,2})?)(?!\d|[.,]\d)(?:\s+(mil)\b)?", re.I)
NUMBER_WORDS = dict(zip("um dois tres quatro cinco seis sete oito nove dez onze doze".split(), range(1, 13)))
COUNT = r"\d+|" + "|".join(NUMBER_WORDS)
INSTALLMENTS = re.compile(r"\b(\d+)\s*(?:x|parcelas|vezes)\b")
CATEGORIES = {
    "alimentacao": ("alimentacao", "proteina", "mercado", "lanche", "restaurante", "ifood", "padaria"),
    "moradia": ("moradia", "aluguel", "energia", "luz", "internet", "condominio", "agua"),
    "transporte": ("transporte", "onibus", "metro", "uber", "moto", "gasolina", "passagem", "salvador card", "99"),
    "saude": ("academia", "saude", "farmacia", "medico"),
    "lazer": ("lazer", "cinema", "cinemark", "spotify", "youtube", "netflix"),
    "educacao": ("concurso", "curso", "faculdade", "escola"),
    "impostos": ("das mei", "imposto", "tributo"),
    "dividas": ("divida", "parcela", "emprestimo"),
}


def norm(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))


def cents(raw, multiplier=1):
    raw = raw.replace(".", "").replace(",", ".") if "," in raw else raw
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", raw):
        raw = raw.replace(".", "")
    try:
        value = Decimal(raw) * multiplier
        if not value.is_finite() or not 0 < value <= Decimal("100000000"):
            raise ValueError("valor fora do limite")
        return int((value * 100).quantize(Decimal("1")))
    except InvalidOperation as exc:
        raise ValueError("valor invalido") from exc


def brl(value):
    return ("R$ " + f"{Decimal(value)/100:,.2f}").replace(",", "_").replace(".", ",").replace("_", ".")


def month_add(month, n):
    y, m = map(int, month.split("-"))
    k = y * 12 + m - 1 + n
    return f"{k//12:04d}-{k%12+1:02d}"


def category(name, kind):
    if kind == "income":
        return "renda"
    n = norm(name)
    return next((cat for cat, words in CATEGORIES.items() if any(re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", n) for w in words)), "outras")


def get_month(text, today):
    n = norm(text)
    iso = re.search(r"\b(20\d{2})-(0[1-9]|1[0-2])(?:-\d{2})?\b", n)
    if iso:
        return iso.group(1) + "-" + iso.group(2)
    if "mes passado" in n or "mes anterior" in n:
        return month_add(today.strftime("%Y-%m"), -1)
    if "proximo mes" in n or "mes que vem" in n:
        return month_add(today.strftime("%Y-%m"), 1)
    name = NAMED_MONTH.search(n)
    if name:
        return f"{int(name.group(2) or today.year):04d}-{MONTHS.index(name.group(1)) + 1:02d}"
    return today.strftime("%Y-%m")


def get_day(text, today):
    n = norm(text)
    if re.search(r"\bdepois de amanha\b", n):
        return today + timedelta(days=2)
    if re.search(r"\banteontem\b", n):
        return today - timedelta(days=2)
    if re.search(r"\bontem\b", n):
        return today - timedelta(days=1)
    if re.search(r"\bamanha\b", n):
        return today + timedelta(days=1)
    if re.search(r"\bhoje\b", n):
        return today
    iso = re.search(r"\b20\d{2}-\d{2}-\d{2}\b", n)
    if iso:
        return date.fromisoformat(iso.group())
    match = re.search(r"(?<![\d-])(\d{1,2})[-/](\d{1,2})(?:[-/](20\d{2}))?\b", n)
    if match:
        return date(int(match.group(3) or today.year), int(match.group(2)), int(match.group(1)))
    match = LONG_DATE.search(n)
    if match:
        return date(int(match.group(3) or today.year), MONTHS.index(match.group(2)) + 1, int(match.group(1)))
    match = re.search(r"\bdia\s+(\d{1,2})\b", n)
    if match:
        return date.fromisoformat(get_month(text, today) + f"-{int(match.group(1)):02d}")
    return None


@dataclass
class Item:
    name: str
    amount_cents: int
    kind: str
    payer: str
    frequency: str
    month: str
    day: str | None = None
    months: int | None = None
    category: str = "outras"
    account: str | None = None
    payer_name: str | None = None
    until: str | None = None
    installments: int | None = None
    personal_cents: int | None = None
    goal: bool = False


def money_matches(text):
    text = re.sub(r"\b20\d{2}-\d{2}-\d{2}\b|(?<![\d-])\d{1,2}[-/]\d{1,2}(?:[-/]20\d{2})?\b", "", text)
    text = re.sub(r"\b(?:na|no|pela|pelo|de|da|do)\s+99\b", "", text)
    text = LONG_DATE.sub("", text)
    text = re.sub(r"\bdia\s+\d{1,2}\b", "", text)
    text = re.sub(r"\b\d+\s*(?:dias?|semanas?|mes(?:es)?|anos?|parcelas?|vezes|x)\b", "", text)
    text = re.sub(r"\b(" + "|".join(MONTHS) + r")(?:\s+de)?\s+20\d{2}\b", r"\1", text)
    return text, list(MONEY.finditer(text))


def responsible_party(text):
    match = re.search(r"\b(?:pago[sa]?|paga[sa]?|dividid[oa])\s+(?:pelo|pela|por|com)\s+([^,.;]+)", text)
    value = match.group(1) if match else ""
    subject = re.search(r"\b(meu pai|minha mae|meu irmao|minha irma|meu parceiro|minha parceira|terceiros)\b", text)
    if subject:
        return subject.group()
    if value and not re.match(r"(?:mim|mes)\b", value):
        return re.split(r"\s+(?:hoje|ontem|amanha|em|no|na|todo|por)\b|\s+r\$", value)[0][:100].strip()
    return None


def occurrence_dates(item):
    """Return explicitly dated occurrences for a finite commitment."""
    if not item.get("day"):
        return []
    first = date.fromisoformat(item["day"])
    count = item.get("installments") or item.get("months")
    if count:
        step = 12 if item["frequency"] == "yearly" else 1
        dates = []
        for index in range(count):
            year, month = map(int, month_add(first.strftime("%Y-%m"), step * index).split("-"))
            dates.append(date(year, month, min(first.day, monthrange(year, month)[1])))
        return dates
    if item["frequency"] == "once":
        return [first]
    if not item.get("until"):
        return []
    end = date.fromisoformat(item["until"])
    if item["frequency"] == "weekly":
        return [first + timedelta(weeks=index) for index in range((end - first).days // 7 + 1)]
    month_count = (end.year - first.year) * 12 + end.month - first.month
    step = 12 if item["frequency"] == "yearly" else 1
    return [day for day in occurrence_dates(dict(item, months=month_count // step + 1)) if day <= end]


def installment_amounts(total, count):
    amount, remainder = divmod(total, count)
    return [amount + (index < remainder) for index in range(count)]


def interpret(message, today):
    """Return draft items and unresolved lines; never mutate storage."""
    items, unresolved = [], []
    section, owner, monthly, section_payer = "", "self", False, None
    section_planned = False
    account = None
    footer = re.search(r"(?:^|\n)\s*(despesas|gastos|receitas)\s*$", norm(message))
    if footer:
        section = "income" if footer.group(1) == "receitas" else "expense"
    lines = re.split(r"\r?\n|;(?!\s*minha parte\b)", message, flags=re.I)
    for raw in lines:
        line = raw.strip().strip("*").strip()
        if not line:
            continue
        line = re.sub(r"^\s*(?:[-•]\s*|\d+[.)]\s+)", "", line).replace("**", "")
        n = norm(line)
        # Section headers carry context, but instructions/totals do not become money.
        if re.match(r"^(regras|objetivo|instrucoes|observacoes)\b", n) and not MONEY.search(n):
            section = "ignore"
            continue
        if re.match(r"^(minha renda|receitas?|renda|despesas|gastos|meus gastos|orcamento|metas|compromissos|dividas|pagos por|planejamento)", n) and not MONEY.search(n) and len(n) < 100:
            section_planned = bool(re.search(r"\bprevist[oa]s?\b|\bplanejad[oa]s?\b|\ba (?:receber|pagar)\b|^(?:compromissos|dividas|planejamento)\b", n))
            section_payer = responsible_party(n)
            owner = "third" if section_payer or re.search(r"terceiro|outras pessoas", n) else "self"
            monthly = bool(re.search(r"\bmens(?:al|ais)\b|\bpor mes\b", n))
            section = "income" if n.startswith(("minha renda", "renda", "receita")) else ("budget" if n.startswith(("orcamento", "meta")) else "expense")
            if n.startswith(("compromissos", "dividas")):
                monthly = False
            continue
        if section == "ignore":
            continue
        if re.match(r"^(conta de recebimento|recebimento pela conta|recebimento em|conta bancaria)\b", n):
            account = line.split(":", 1)[-1].strip() if ":" in line else re.sub(r"(?i)^recebimento pela conta\s*", "", line).strip()
            for item in items:
                if item.kind == "income" and item.account is None:
                    item.account = account[:100]
            continue
        if re.match(r"^(duracao do contrato|duracao|prazo do contrato)\b", n):
            duration = re.search(r"\b(\d+)\s*mes", n)
            if duration and items and items[-1].kind == "income" and items[-1].frequency == "monthly" and 1 <= int(duration.group(1)) <= 120:
                items[-1].months = int(duration.group(1))
            else:
                unresolved.append(line)
            continue
        if re.match(r"^(quero|nao|antes|depois|meu objetivo|o objetivo|vou informar|identifique|separe|pergunte|desconte|total|subtotal|saldo)\b", n) and not re.search(r"\b(cadastrar|registrar|lancar|guardar|gastar|planejar)\b.*r\$", n):
            continue
        if re.match(r"^\d+\.\s", n) and "r$" not in n:
            continue
        # Dates and installment counts are not monetary amounts.
        stripped, matches = money_matches(n)
        if not matches:
            if re.search(r"\b(gastei|paguei|recebi|ganhei|registrar|cadastrar|despesa|receita)\b", n):
                unresolved.append(line)
            continue
        split = INSTALLMENTS.search(n)
        shared = bool(re.search(r"\b(?:compartilhad[oa]|dividid[oa]|divido|minha parte)\b", n))
        personal = None
        if shared and len(matches) == 2:
            share = re.search(r"\bminha parte\b", stripped)
            if share and matches[0].end() < share.start() < matches[1].start():
                try:
                    personal = cents(matches[1].group(1), 1000 if matches[1].group(2) else 1)
                    matches = matches[:1]
                except ValueError:
                    pass
        if len(matches) > 1:
            # Explicit month-by-month amounts: repeat the name with each amount.
            segments = re.split(r"\s+e\s+(?=r\$\s*\d)", line, flags=re.I)
            if len(segments) == 2 and ":" in segments[0]:
                label = segments[0].split(":", 1)[0]
                sub, issues = interpret((label + ": " + segments[0].split(":", 1)[1]) + "\n" + label + ": " + segments[1], today)
                if len(sub) == 2 and not issues:
                    items.extend(sub)
                    continue
            unresolved.append(line + " (use um valor por linha)")
            continue
        match = matches[0]
        if re.search(r"-\s*r?\$?\s*\d", stripped) and not re.search(r"\w\s+-\s+\d", stripped):
            unresolved.append(line + " (valor negativo ou ambiguo)")
            continue
        try:
            amount = cents(match.group(1), 1000 if match.group(2) else 1)
            day = get_day(line, today)
            end = re.search(r"\b(?:ate|termina em)\s+(20\d{2}-\d{2}-\d{2}|\d{1,2}/\d{1,2}(?:/20\d{2})?)\b", n)
            until = get_day(end.group(1), today) if end else None
        except (ValueError, OverflowError):
            unresolved.append(line + " (valor ou data invalida)")
            continue
        has_month = any(re.search(r"\b" + m + r"\b", n) for m in MONTHS) or "proximo mes" in n or "mes passado" in n
        is_weekly = bool(re.search(r"semanal|por semana|toda semana|cada semana", n))
        is_yearly = bool(re.search(r"anual|por ano|todo ano|cada ano", n))
        is_monthly = bool(re.search(r"mens(?:al(?:mente)?|ais)|por mes|/mes|todo mes|cada mes", n)) or (
            monthly and not has_month and not day and not is_weekly and not is_yearly
        )
        duration = re.search(r"\b(" + COUNT + r")\s*mes(?:es)?\b", n)
        months = (NUMBER_WORDS.get(duration.group(1)) or int(duration.group(1))) if duration else None
        if months is not None and not 1 <= months <= 120:
            unresolved.append(line + " (duracao invalida)")
            continue
        father_card = bool(re.search(r"\bcartao (?:do meu|do) pai\b", n))
        payer_name = ("Pai" if father_card else responsible_party(n)) or section_payer
        payer = "shared" if shared else "third" if payer_name else owner
        if re.search(r"por mim|eu pago", n):
            if not shared:
                payer, payer_name = "self", None
        if re.search(r"\b(reserva|guardar|poupar|economizar|meta)\b", n) and not re.search(r"\b(gastei|paguei)\b", n):
            kind = "reserve"
        elif re.search(r"\b(limite|orcamento|teto)\b", n) or section == "budget":
            kind = "budget"
        elif re.search(r"\b(recebi|receby|ganhei|receber|salario|receita|renda|contrato pj|freelance|freela)\b", n) or section == "income":
            kind = "income"
        else:
            kind = "expense"
        installment_count = int(split.group(1)) if split else None
        recurring = is_monthly or is_weekly or is_yearly
        future_language = bool(re.search(
            r"\b(?:previst[oa]s?|planejad[oa]s?|agendad[oa]s?|previsao|planejamento|"
            r"futur[oa]s?|vence|vencimento|planeje|agende)\b|"
            r"\b(?:vou|vai|sera|devera|irei|devo)\s+(?:receber|ganhar|pagar|gastar|comprar|"
            r"depositar|cair|ser|depositad[oa]|creditad[oa])\b|"
            r"\ba (?:receber|pagar|ser depositad[oa])\b|^divida\b", n
        ))
        completed = bool(re.search(
            r"\b(?:gastei|paguei|comprei|recebi|ganhei|pago|pagou|recebid[oa]|depositad[oa]|"
            r"depositaram|creditad[oa]|caiu|ja paga|gaste|receby)\b", n
        ))
        denied = re.search(
            r"\bnao\s+(?:(?:foi|esta|fui|tinha sido|foi ainda)\s+)?"
            r"(?:gastei|paguei|pagou|pag[oa]|recebi|ganhei|comprei|caiu|"
            r"depositaram|depositad[oa]|creditad[oa]|recebid[oa])\b", n
        )
        if denied:
            unresolved.append(line + " (confirme se deseja cadastrar uma previsão)")
            continue
        period = get_month(line, today)
        dated_future = day > today if day else period > today.strftime("%Y-%m")
        projected = future_language or section_planned or (
            not completed and (dated_future or until is not None or re.search(r"\ba partir de\b", n))
        )
        actual = kind in ("income", "expense") and not projected and not split
        if (actual and payer != "self" and not completed and not day
                and re.search(r"\bpaga\b", n)):
            unresolved.append(line + " (informe se a despesa já foi paga ou é uma previsão)")
            continue
        if actual and recurring:
            # A frequência sozinha não transforma uma movimentação em previsão.
            is_weekly = is_monthly = is_yearly = recurring = False
            months = until = None
        if installment_count is not None and (kind != "expense" or payer != "self" or recurring or day is None or not 2 <= installment_count <= min(amount, 120)):
            unresolved.append(line + " (informe entre 2 e 120 parcelas e a data do primeiro vencimento)")
            continue
        if not split and re.search(r"\bparcelad[oa]\b", n):
            unresolved.append(line + " (informe o número de parcelas e a data do primeiro vencimento)")
            continue
        if shared and (personal is None or not 0 < personal < amount or kind != "expense"):
            unresolved.append(line + " (informe o total e o valor da sua parte)")
            continue
        if until and (not day or until < day or (until - day).days > 3660 or months):
            unresolved.append(line + " (confira o início e o término da recorrência)")
            continue
        if (is_weekly and (not day or months)) or (is_yearly and months):
            unresolved.append(line + " (informe a data de início e, se houver, a data de término)")
            continue
        if actual and day is None and not has_month:
            day = today
        if actual and day is None:
            unresolved.append(line + " (informe o dia do lançamento efetivo)")
            continue
        if actual and day > today:
            unresolved.append(line + " (data futura: especifique que e previsto)")
            continue
        goal = kind == "reserve" and not recurring and bool(re.search(r"\bmeta\b", n) or day and re.search(r"\bate\b", n))
        if not actual and not recurring and day is None and not has_month and not goal:
            # Do not infer the due date of a commitment.
            unresolved.append(line + " (informe o mes, a data ou se e mensal)")
            continue
        if ":" in line:
            name = line.split(":", 1)[0].strip()
        else:
            name = re.sub(r"\b20\d{2}-\d{2}-\d{2}\b|(?<![\d-])\d{1,2}[-/]\d{1,2}(?:[-/]20\d{2})?\b", "", line)
            name = re.sub(r"(?i)\b(?:vou|meu pai|minha mãe|meu irmão)\s+(?:receber|pagar|pagou|paga)\b", "", name)
            name = re.sub(r"(?i)\b(?:durante|por)\s+(?:" + COUNT + r")\s+mes(?:es)?\b|\b(?:em\s+)?\d+\s*(?:x|parcelas|vezes)\b", "", name)
            name = re.sub(r"\b99\b", "APPNOVENOVE", name)
            name = MONEY.sub("", name)
            name = name.replace("APPNOVENOVE", "99")
            name = re.sub(r"(?i)\b(?:por mês|todo mês|cada mês|primeiro vencimento|primeira parcela|que custa|meu trabalho)\b", lambda m: "Trabalho" if m.group().lower() == "meu trabalho" else "", name)
            name = re.sub(r"(?i)\b(gastei|gaste|paguei|comprei|recebi|receby|ganhei|vou|receber|bota|coloca|lança|adicionar|registrar|cadastrar|planejar|despesa|receita|reais|conto[s]?|hoje|ontem|amanhã|mensal|mensais)\b", " ", name)
            name = re.sub(r"(?i)^\s*(?:(?:de|do|da|no|na|em|para|com|minha|meu|uma|um)\s+)+", "", name)
            name = re.sub(r"(?i)(?:\s+(?:em|no|na|para|com|começando|até|dia|de))+\s*[.,]*\s*$", "", name)
            name = re.sub(r"\s+", " ", name).strip(" -/.,")
        if norm(name).strip() == "passagem salvador card":
            name = "Salvador Card"
        elif norm(name).strip() == "uber moto":
            name = "Uber Moto"
        if not name and kind == "income" and recurring:
            name = "Receita prevista"
        if not name or len(name) > 180 or norm(name) in {"gasto", "boleto", "conta", "valor"}:
            unresolved.append(line + " (informe a descricao)")
            continue
        if payer != "self" and kind in ("income", "reserve", "budget"):
            unresolved.append(line + " (confirme a responsabilidade e o tipo)")
            continue
        if goal and day and day < today:
            unresolved.append(line + " (a data da meta precisa ser hoje ou posterior)")
            continue
        frequency = "weekly" if is_weekly else "yearly" if is_yearly else "monthly" if is_monthly else "once"
        items.append(Item(name=name, amount_cents=amount, kind=kind, payer=payer,
                          frequency="actual" if actual else frequency,
                          month=day.strftime("%Y-%m") if day else period,
                          day=day.isoformat() if day else None, months=months if is_monthly else None,
                          category=category(name, kind), account=account if kind == "income" else "Cartão do pai" if father_card and payer != "self" else None,
                          payer_name=payer_name, until=until.isoformat() if until else None,
                          installments=installment_count, personal_cents=personal, goal=goal))
    return items, unresolved


def occurrence_count(item, month):
    frequency = item["frequency"]
    if month < item["month"] or item.get("until") and month > item["until"][:7]:
        return 0
    if frequency == "monthly":
        return int(not item.get("months") or month < month_add(item["month"], item["months"]))
    if frequency == "yearly":
        return int(month[-2:] == item["month"][-2:])
    if frequency == "weekly":
        start = date.fromisoformat(item["day"])
        first = date.fromisoformat(month + "-01")
        end = date.fromisoformat(month_add(month, 1) + "-01") - timedelta(days=1)
        if item.get("until"):
            end = min(end, date.fromisoformat(item["until"]))
        next_day = start + timedelta(weeks=max(0, ((first - start).days + 6) // 7))
        return max(0, (end - next_day).days // 7 + 1)
    return int(item["month"] == month)


def occurs(item, month):
    return occurrence_count(item, month) > 0


def due_dates_in_month(item, month):
    count = occurrence_count(item, month)
    if not item.get("day") or count == 0:
        return []
    start = date.fromisoformat(item["day"])
    year, number = map(int, month.split("-"))
    if item["frequency"] == "weekly":
        first = date(year, number, 1)
        next_day = start + timedelta(weeks=max(0, ((first - start).days + 6) // 7))
        return [next_day + timedelta(weeks=index) for index in range(count)]
    return [date(year, number, min(start.day, monthrange(year, number)[1]))]


def plan_totals(items, month):
    out = dict(income=0, expense=0, third=0, budget=0, reserve=0, third_actual=0)
    for item in items:
        count = occurrence_count(item, month)
        if not count:
            continue
        total = item["amount_cents"] * count
        personal = item.get("personal_cents")
        if item["frequency"] == "actual":
            if item["kind"] == "expense" and item["payer"] in ("third", "shared"):
                out["third_actual"] += total - (personal or 0)
            continue
        if item["payer"] == "shared":
            out["expense"] += personal * count
            out["third"] += total - personal * count
            continue
        key = "third" if item["payer"] == "third" else item["kind"]
        out[key] += total
    return out


def item_key(item):
    return (norm(item["name"]).strip(), item["amount_cents"], item["kind"], item["payer"],
            item["frequency"], item["month"], item.get("day"), item.get("months"))
