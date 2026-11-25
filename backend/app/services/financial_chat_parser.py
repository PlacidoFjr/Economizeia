"""Deterministic, conservative Portuguese financial chat interpretation.

No model output or browser-provided history can authorize a write.
Amounts are parsed as integer BRL cents. Ambiguous input is not committed.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import re
import unicodedata

MONTHS = ("janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro").split()
MONEY = re.compile(r"(?<![\d.,])(?:r\$\s*)?(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:[,.]\d{1,2})?)(?![\d.,])", re.I)
CATEGORIES = {
    "alimentacao": ("alimentacao", "proteina", "mercado", "lanche", "restaurante", "ifood", "padaria"),
    "moradia": ("moradia", "aluguel", "energia", "luz", "internet", "condominio", "agua"),
    "transporte": ("transporte", "onibus", "metro", "uber", "moto", "gasolina"),
    "saude": ("academia", "saude", "farmacia", "medico"),
    "lazer": ("lazer", "cinema", "cinemark", "spotify", "youtube", "netflix"),
    "educacao": ("concurso", "curso", "faculdade", "escola"),
    "impostos": ("das mei", "imposto", "tributo"),
    "dividas": ("divida", "parcela", "emprestimo"),
}


def norm(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))


def cents(raw):
    raw = raw.replace(".", "").replace(",", ".") if "," in raw else raw
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", raw):
        raw = raw.replace(".", "")
    try:
        value = Decimal(raw)
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
    return next((cat for cat, words in CATEGORIES.items() if any(w in n for w in words)), "outras")


def get_month(text, today):
    n = norm(text)
    iso = re.search(r"\b(20\d{2})-(0[1-9]|1[0-2])(?:-\d{2})?\b", n)
    if iso:
        return iso.group(1) + "-" + iso.group(2)
    if "mes passado" in n or "mes anterior" in n:
        return month_add(today.strftime("%Y-%m"), -1)
    if "proximo mes" in n or "mes que vem" in n:
        return month_add(today.strftime("%Y-%m"), 1)
    for i, m in enumerate(MONTHS, 1):
        if re.search(r"\b" + m + r"\b", n):
            year = re.search(r"\b20\d{2}\b", n)
            return f"{int(year.group()) if year else today.year:04d}-{i:02d}"
    return today.strftime("%Y-%m")


def get_day(text, today):
    n = norm(text)
    if re.search(r"\bontem\b", n):
        return today - timedelta(days=1)
    if re.search(r"\bamanha\b", n):
        return today + timedelta(days=1)
    if re.search(r"\bhoje\b", n):
        return today
    iso = re.search(r"\b20\d{2}-\d{2}-\d{2}\b", n)
    if iso:
        return date.fromisoformat(iso.group())
    match = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(20\d{2}))?\b", n)
    if match:
        return date(int(match.group(3) or today.year), int(match.group(2)), int(match.group(1)))
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


def interpret(message, today):
    """Return draft items and unresolved lines; never mutate storage."""
    items, unresolved = [], []
    section, owner, monthly = "", "self", False
    account = None
    lines = re.split(r"\n|;", message)
    for raw in lines:
        line = raw.strip().strip("*").strip()
        if not line:
            continue
        line = re.sub(r"^\s*[-•]\s*", "", line).replace("**", "")
        n = norm(line)
        # Section headers carry context, but instructions/totals do not become money.
        if re.match(r"^(regras|objetivo|instrucoes|observacoes)\b", n) and not MONEY.search(n):
            section = "ignore"
            continue
        if re.match(r"^(minha renda|receitas?|renda|despesas|gastos|meus gastos|orcamento|metas|compromissos|dividas|pagos por)", n) and not MONEY.search(n) and len(n) < 100:
            owner = "third" if re.search(r"pai|mae|terceiro|outras pessoas", n) else "self"
            monthly = "mens" in n or n.startswith(("minha renda", "renda", "receita", "despesas pagas", "meus gastos", "orcamento"))
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
            if duration and items and items[-1].kind == "income" and 1 <= int(duration.group(1)) <= 120:
                items[-1].months = int(duration.group(1))
            else:
                unresolved.append(line)
            continue
        if re.match(r"^(quero|nao|antes|depois|meu objetivo|o objetivo|vou informar|identifique|separe|pergunte|desconte|total|subtotal|saldo)\b", n) and not re.search(r"\b(cadastrar|registrar|lancar|guardar|gastar|planejar)\b.*r\$", n):
            continue
        if re.match(r"^\d+\.\s", n) and "r$" not in n:
            continue
        # Dates and installment counts are not monetary amounts.
        stripped = re.sub(r"\b20\d{2}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}(?:/20\d{2})?\b", "", n)
        stripped = re.sub(r"\b\d+\s*(?:mes(?:es)?|parcelas?|vezes|x)\b", "", stripped)
        stripped = re.sub(r"\b20\d{2}\b", "", stripped)
        matches = list(MONEY.finditer(stripped))
        if not matches:
            if re.search(r"\b(gastei|paguei|recebi|ganhei|registrar|cadastrar|despesa|receita)\b", n):
                unresolved.append(line)
            continue
        if re.search(r"\b(?:\d+\s*(?:x|parcelas?|vezes)|parcelad[oa])\b", n):
            unresolved.append(line + " (informe cada parcela, valor e vencimento separadamente)")
            continue
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
            amount = cents(match.group(1))
            day = get_day(line, today)
        except (ValueError, OverflowError):
            unresolved.append(line + " (valor ou data invalida)")
            continue
        has_month = any(re.search(r"\b" + m + r"\b", n) for m in MONTHS) or "proximo mes" in n or "mes passado" in n
        is_monthly = bool(re.search(r"mensal|por mes|/mes|todo mes|cada mes", n)) or (monthly and not has_month and not day)
        duration = re.search(r"\b(\d+)\s*mes(?:es)?\b", n)
        months = int(duration.group(1)) if duration else None
        if months is not None and not 1 <= months <= 120:
            unresolved.append(line + " (duracao invalida)")
            continue
        payer = "third" if re.search(r"pag[ao]s? (?:pelo|pela|por)|meu pai|minha mae|terceiros", n) else owner
        if re.search(r"por mim|eu pago", n):
            payer = "self"
        if re.search(r"\b(reserva|guardar|poupar|economizar)\b", n) and not re.search(r"\b(gastei|paguei)\b", n):
            kind = "reserve"
        elif re.search(r"\b(limite|orcamento|teto)\b", n) or section == "budget":
            kind = "budget"
        elif re.search(r"\b(recebi|ganhei|salario|receita|renda|contrato pj|freelance|freela)\b", n) or section == "income":
            kind = "income"
        else:
            kind = "expense"
        actual = bool(re.search(r"\b(gastei|paguei|comprei|recebi|ganhei|pago|pagou|recebido|ja paga)\b", n)) and not is_monthly and not re.search(r"\b(previsto|prevista|planejado|planejada|futuro|vou|limite)\b", n)
        if re.search(r"\bnao\s+(?:gastei|paguei|pagou|pago|recebi|ganhei|comprei)\b", n):
            unresolved.append(line + " (confirme se a despesa ou receita e apenas prevista)")
            continue
        if kind in ("reserve", "budget"):
            actual = False
        if actual and day is None and not has_month:
            day = today
        if actual and day is None:
            unresolved.append(line + " (informe o dia do lançamento efetivo)")
            continue
        if actual and day > today:
            unresolved.append(line + " (data futura: especifique que e previsto)")
            continue
        if not actual and not is_monthly and day is None and not has_month:
            # Do not infer the due date of a commitment.
            unresolved.append(line + " (informe o mes, a data ou se e mensal)")
            continue
        if ":" in line:
            name = line.split(":", 1)[0].strip()
        else:
            name = re.sub(r"(?i)r\$\s*", "", line)
            name = re.sub(r"(?i)\b\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?\b|\b\d+(?:[,.]\d{1,2})?\b", "", name)
            name = re.sub(r"(?i)\b(gastei|paguei|comprei|recebi|ganhei|adicionar|registrar|cadastrar|planejar|despesa|receita|reais|hoje|ontem|amanhã|de|no|na|em|para|com|mensal|mensais)\b", " ", name)
            name = re.sub(r"\s+", " ", name).strip(" -/.,")
        if not name or len(name) > 180 or norm(name) in {"gasto", "boleto", "conta", "valor"}:
            unresolved.append(line + " (informe a descricao)")
            continue
        if payer == "third" and kind in ("income", "reserve", "budget"):
            unresolved.append(line + " (confirme a responsabilidade e o tipo)")
            continue
        items.append(Item(name=name, amount_cents=amount, kind=kind, payer=payer,
                          frequency="actual" if actual else ("monthly" if is_monthly else "once"),
                          month=day.strftime("%Y-%m") if day else get_month(line, today),
                          day=day.isoformat() if day else None, months=months if is_monthly else None,
                          category=category(name, kind), account=account if kind == "income" else None))
    return items, unresolved


def occurs(item, month):
    if item["frequency"] != "monthly":
        return item["month"] == month
    return item["month"] <= month and (not item.get("months") or month < month_add(item["month"], item["months"]))


def plan_totals(items, month):
    out = dict(income=0, expense=0, third=0, budget=0, reserve=0, third_actual=0)
    for item in items:
        if not occurs(item, month):
            continue
        if item["frequency"] == "actual":
            if item["kind"] == "expense" and item["payer"] == "third":
                out["third_actual"] += item["amount_cents"]
            continue
        key = "third" if item["payer"] == "third" else item["kind"]
        out[key] += item["amount_cents"]
    return out


def item_key(item):
    return (norm(item["name"]).strip(), item["amount_cents"], item["kind"], item["payer"],
            item["frequency"], item["month"], item.get("day"), item.get("months"))
