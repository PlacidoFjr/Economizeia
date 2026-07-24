import logging
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from dateutil.relativedelta import relativedelta  # type: ignore
from sqlalchemy.orm import Session

from app.db.models import Bill, BillStatus, BillType, Investment, SavingsGoal, User
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


@dataclass
class LocalChatResult:
    response: str
    action: str = "chat"
    bill_id: Optional[str] = None


class LocalChatbotService:
    """Deterministic chatbot layer that avoids AI for common flows."""

    EXPENSE_KEYWORDS = [
        "despesa", "gasto", "gastei", "paguei", "pagamento", "boleto",
        "conta", "comprei", "compra", "saida", "pix", "pago", "paga",
    ]
    INCOME_KEYWORDS = [
        "receita", "recebi", "ganhei", "entrada", "salario", "renda",
        "freelance", "freela", "vendas", "comissao", "bonus",
    ]
    CATEGORY_KEYWORDS = {
        "alimentacao": ["mercado", "supermercado", "restaurante", "ifood", "lanche", "padaria", "comida", "acougue"],
        "moradia": ["aluguel", "condominio", "agua", "luz", "energia", "gas", "internet", "iptu"],
        "transporte": ["uber", "99", "taxi", "gasolina", "combustivel", "onibus", "metro", "pedagio"],
        "saude": ["farmacia", "medico", "remedio", "hospital", "dentista", "consulta"],
        "vestuario": ["roupa", "roupas", "tenis", "sapato", "camisa", "calca"],
        "compras": ["loja", "shopping", "compras"],
        "lazer": ["cinema", "show", "festa", "jogo", "lazer"],
        "educacao": ["curso", "faculdade", "escola", "livro"],
        "investimentos": ["salario", "freelance", "freela", "vendas", "comissao", "bonus", "dividendo"],
    }
    FILLER_WORDS = {
        "adiciona", "adicionar", "add", "registra", "registrar", "cria", "criar",
        "coloca", "lanca", "lancar", "ai", "uma", "um", "de", "do", "da", "no",
        "na", "em", "para", "com", "foi", "gasto", "gastei", "despesa", "paguei",
        "pagamento", "compra", "comprei", "receita", "recebi", "ganhei", "entrada",
        "reais", "real", "r", "hoje", "ontem", "amanha", "boleto", "conta", "pago", "paga",
    }

    STATIC_RESPONSES = {
        "greeting": "Oi! Posso te ajudar a consultar seus gastos, contas pendentes, vencimentos ou registrar receitas e despesas.",
        "help": (
            "Posso responder sem IA sobre seu financeiro: contas pendentes, vencidas, saldo do mês, "
            "gastos por categoria, próximos vencimentos e também registrar frases como "
            "'gastei R$ 35 no Uber' ou 'recebi R$ 2500 salário'."
        ),
        "upload": "O upload de boleto está desativado. Registre seus gastos pelo chat, por exemplo: 'R$ 200 boleto pago', ou use a tela Adicionar.",
        "expense_help": "Para adicionar uma despesa, escreva algo como: 'gastei R$ 35 no Uber' ou 'paguei R$ 120 de energia'.",
        "month_navigation": "Para conferir outro mês, use as setas no topo do Painel, Finanças, Pagamentos ou Parcelados. O chat resume o mês atual; as telas mostram o histórico por mês.",
    }

    def try_handle(
        self,
        message: str,
        current_user: User,
        db: Session,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[LocalChatResult]:
        normalized = cache_service.normalize_message(message)
        has_pending_conversation = bool(conversation_history)

        command_result = self._try_transaction_command(normalized, message, current_user, db)
        if command_result:
            return command_result

        followup_result = self._try_pending_transaction_followup(
            normalized=normalized,
            original_message=message,
            current_user=current_user,
            db=db,
            conversation_history=conversation_history or [],
        )
        if followup_result:
            return followup_result

        static_intent = self._detect_static_intent(normalized)
        if static_intent:
            cached = cache_service.get_cached_response(
                str(current_user.id), message, cache_type=f"static:{static_intent}"
            )
            if cached:
                return LocalChatResult(response=cached, action="chat")

            response = self.STATIC_RESPONSES[static_intent]
            if cache_service.is_cacheable_message(message, action="chat", has_pending_conversation=has_pending_conversation):
                cache_service.set_cached_response(
                    str(current_user.id),
                    message,
                    response,
                    ttl=None,
                    cache_type=f"static:{static_intent}",
                )
            return LocalChatResult(response=response, action="chat")

        financial_intent = self._detect_financial_intent(normalized)
        if financial_intent:
            context = self.build_financial_context(current_user, db)
            context_hash = cache_service.get_context_hash(context)
            cached = cache_service.get_cached_response(
                str(current_user.id),
                message,
                context_hash=context_hash,
                cache_type=f"financial:{financial_intent}",
            )
            if cached:
                return LocalChatResult(response=cached, action="financial_summary")

            response = self._answer_financial_intent(financial_intent, context)
            if cache_service.is_cacheable_message(
                message,
                action="financial_summary",
                has_pending_conversation=has_pending_conversation,
                requires_context=True,
            ):
                cache_service.set_cached_response(
                    str(current_user.id),
                    message,
                    response,
                    context_hash=context_hash,
                    ttl=None,
                    cache_type=f"financial:{financial_intent}",
                )
            return LocalChatResult(response=response, action="financial_summary")

        return None

    def build_financial_context(self, current_user: User, db: Session) -> Dict[str, Any]:
        today = date.today()
        user_bills = db.query(Bill).filter(Bill.user_id == current_user.id).all()
        savings_goals = db.query(SavingsGoal).filter(SavingsGoal.user_id == current_user.id).all()
        investments = db.query(Investment).filter(Investment.user_id == current_user.id).all()

        pending_bills = [b for b in user_bills if b.status in [BillStatus.PENDING, BillStatus.CONFIRMED]]
        confirmed_bills = [b for b in user_bills if b.status == BillStatus.CONFIRMED]
        scheduled_bills = [b for b in user_bills if b.status == BillStatus.SCHEDULED]
        paid_bills = [b for b in user_bills if b.status == BillStatus.PAID]
        overdue_bills = [b for b in user_bills if b.due_date and b.due_date < today and b.status != BillStatus.PAID]

        current_month = today.month
        current_year = today.year
        current_month_label = self._format_month_label(today)
        monthly_expenses = sum(
            b.amount or 0
            for b in user_bills
            if b.due_date and b.due_date.month == current_month and b.due_date.year == current_year
            and b.type == BillType.EXPENSE and b.status in [BillStatus.PAID, BillStatus.CONFIRMED]
        )
        monthly_income = sum(
            b.amount or 0
            for b in user_bills
            if b.due_date and b.due_date.month == current_month and b.due_date.year == current_year
            and b.type == BillType.INCOME and b.status in [BillStatus.PAID, BillStatus.CONFIRMED]
        )

        categories: Dict[str, Dict[str, Any]] = {}
        for bill in user_bills:
            if (
                bill.type != BillType.EXPENSE
                or bill.status not in [BillStatus.PAID, BillStatus.CONFIRMED]
                or not bill.due_date
                or bill.due_date.month != current_month
                or bill.due_date.year != current_year
            ):
                continue
            category = bill.category or "outras"
            if category not in categories:
                categories[category] = {"total": 0.0, "count": 0}
            categories[category]["total"] += bill.amount or 0
            categories[category]["count"] += 1

        next_bills = sorted(
            [b for b in pending_bills if b.due_date],
            key=lambda item: item.due_date or date.max,
        )[:10]

        last_updates = [
            getattr(item, "updated_at", None) or getattr(item, "created_at", None)
            for item in [*user_bills, *savings_goals, *investments]
            if getattr(item, "updated_at", None) or getattr(item, "created_at", None)
        ]
        last_financial_update = max(last_updates).isoformat() if last_updates else None

        return {
            "user_name": current_user.name,
            "total_bills": len(user_bills),
            "pending_bills": len(pending_bills),
            "confirmed_bills": len(confirmed_bills),
            "scheduled_bills": len(scheduled_bills),
            "paid_bills": len(paid_bills),
            "overdue_bills": len(overdue_bills),
            "total_pending": sum(b.amount or 0 for b in pending_bills),
            "total_paid": sum(b.amount or 0 for b in paid_bills),
            "monthly_expenses": monthly_expenses,
            "monthly_income": monthly_income,
            "monthly_balance": monthly_income - monthly_expenses,
            "current_month": f"{current_month}/{current_year}",
            "current_month_label": current_month_label,
            "categories": categories,
            "next_bills": [
                {
                    "issuer": b.issuer or "Desconhecido",
                    "amount": b.amount or 0,
                    "due_date": b.due_date.isoformat() if b.due_date else None,
                    "days_until": (b.due_date - today).days if b.due_date else None,
                    "status": b.status.value,
                    "category": b.category,
                }
                for b in next_bills
            ],
            "overdue_details": [
                {
                    "issuer": b.issuer or "Desconhecido",
                    "amount": b.amount or 0,
                    "due_date": b.due_date.isoformat() if b.due_date else None,
                    "days_overdue": (today - b.due_date).days if b.due_date else 0,
                    "status": b.status.value,
                    "category": b.category,
                }
                for b in overdue_bills
            ],
            "savings_goals_count": len(savings_goals),
            "investments_count": len(investments),
            "investments_total": sum(inv.current_value or inv.amount_invested or 0 for inv in investments),
            "last_financial_update": last_financial_update,
        }

    def _detect_static_intent(self, normalized: str) -> Optional[str]:
        if normalized in {"oi", "ola", "bom dia", "boa tarde", "boa noite"}:
            return "greeting"
        if "upload" in normalized or "enviar boleto" in normalized or "anexar boleto" in normalized:
            return "upload"
        if "mes anterior" in normalized or "mes passado" in normalized or "meses anteriores" in normalized or "historico" in normalized:
            return "month_navigation"
        if "como adicionar despesa" in normalized or "adicionar despesa" == normalized:
            return "expense_help"
        if "ajuda" in normalized or "como funciona" in normalized or "o que voce faz" in normalized or "o que vc faz" in normalized:
            return "help"
        return None

    def _detect_financial_intent(self, normalized: str) -> Optional[str]:
        if "vencid" in normalized or "atrasad" in normalized:
            return "overdue"
        if ("quantos" in normalized or "total" in normalized) and ("boleto" in normalized or "conta" in normalized):
            return "total_bills"
        if "pendente" in normalized or "em aberto" in normalized or "falta pagar" in normalized:
            return "pending"
        if "proxim" in normalized and ("vence" in normalized or "vencimento" in normalized or "conta" in normalized):
            return "next_due"
        if "categoria" in normalized or "maiores gastos" in normalized:
            return "categories"
        if "saldo" in normalized or "como estou" in normalized or "balanco" in normalized:
            return "balance"
        if "quanto gastei" in normalized or "despesas do mes" in normalized or "gastos do mes" in normalized:
            return "monthly_expenses"
        if "quanto recebi" in normalized or "receitas do mes" in normalized:
            return "monthly_income"
        if "investimento" in normalized:
            return "investments"
        if "meta" in normalized or "economia" in normalized:
            return "savings_goals"
        return None

    def _answer_financial_intent(self, intent: str, context: Dict[str, Any]) -> str:
        if intent == "pending":
            return (
                f"Você tem {context['pending_bills']} conta(s) pendente(s), "
                f"totalizando R$ {context['total_pending']:.2f}."
            )
        if intent == "total_bills":
            return (
                f"Você tem {context['total_bills']} conta(s) cadastrada(s): "
                f"{context['pending_bills']} pendente(s), {context['paid_bills']} paga(s) "
                f"e {context['overdue_bills']} vencida(s)."
            )
        if intent == "overdue":
            if context["overdue_bills"] == 0:
                return "Você não tem contas vencidas no momento."
            details = context["overdue_details"][:3]
            items = ", ".join(f"{b['issuer']} R$ {b['amount']:.2f}" for b in details)
            return f"Você tem {context['overdue_bills']} conta(s) vencida(s): {items}."
        if intent == "next_due":
            if not context["next_bills"]:
                return "Não encontrei próximos vencimentos pendentes."
            items = ", ".join(
                f"{b['issuer']} R$ {b['amount']:.2f} em {b['days_until']} dia(s)"
                for b in context["next_bills"][:5]
            )
            return f"Próximos vencimentos: {items}."
        if intent == "categories":
            categories = sorted(
                context["categories"].items(),
                key=lambda item: item[1]["total"],
                reverse=True,
            )[:5]
            if not categories:
                return "Ainda não encontrei despesas categorizadas."
            items = ", ".join(f"{self._format_category_label(name)} R$ {data['total']:.2f}" for name, data in categories)
            return f"Seus maiores gastos por categoria: {items}."
        if intent == "balance":
            return (
                f"Em {context['current_month_label']}, você recebeu R$ {context['monthly_income']:.2f}, "
                f"gastou R$ {context['monthly_expenses']:.2f} e está com saldo de "
                f"R$ {context['monthly_balance']:.2f}."
            )
        if intent == "monthly_expenses":
            return f"Suas despesas de {context['current_month_label']} somam R$ {context['monthly_expenses']:.2f}."
        if intent == "monthly_income":
            return f"Suas receitas de {context['current_month_label']} somam R$ {context['monthly_income']:.2f}."
        if intent == "investments":
            return (
                f"Você tem {context['investments_count']} investimento(s) cadastrado(s), "
                f"com valor atual aproximado de R$ {context['investments_total']:.2f}."
            )
        if intent == "savings_goals":
            return f"Você tem {context['savings_goals_count']} meta(s) de economia cadastrada(s)."
        return self.STATIC_RESPONSES["help"]

    def _try_transaction_command(
        self,
        normalized: str,
        original_message: str,
        current_user: User,
        db: Session,
    ) -> Optional[LocalChatResult]:
        if normalized.startswith(("quanto ", "qual ", "quais ", "tenho ", "me mostra", "mostra ")):
            return None

        is_income = any(keyword in normalized for keyword in self.INCOME_KEYWORDS)
        is_expense = any(keyword in normalized for keyword in self.EXPENSE_KEYWORDS)
        is_command = is_income or is_expense
        if not is_command:
            return None

        amount = self._extract_amount(normalized)
        if amount is None:
            label = "receita" if is_income and not is_expense else "despesa"
            return LocalChatResult(
                response=f"Entendi que você quer registrar uma {label}, mas faltou o valor. Exemplo: R$ 50,00.",
                action="ask_for_info",
            )

        transaction_type = BillType.INCOME if is_income and not is_expense else BillType.EXPENSE
        category = self._detect_category(normalized, transaction_type)
        issuer = self._extract_issuer(normalized, transaction_type)
        status = self._detect_status(normalized)

        if transaction_type == BillType.EXPENSE and ("boleto" in normalized or "conta" in normalized) and status == BillStatus.PAID:
            category = category or "servicos"
            issuer = issuer or ("Boleto pago" if "boleto" in normalized else "Conta paga")

        if transaction_type == BillType.EXPENSE and not category and not issuer:
            return LocalChatResult(
                response=(
                    f"Entendi a despesa de R$ {amount:.2f}. Me diga com o que foi ou onde foi "
                    "(ex: mercado, Uber, energia). Assim eu salvo com categoria e descrição certas."
                ),
                action="ask_for_info",
            )
        if transaction_type == BillType.INCOME and not category and not issuer:
            return LocalChatResult(
                response=(
                    f"Entendi a receita de R$ {amount:.2f}. De onde veio esse dinheiro? "
                    "(ex: salário, freelance, vendas, reembolso)."
                ),
                action="ask_for_info",
            )
        if transaction_type == BillType.INCOME and not category:
            category = "outras"

        due_date = self._extract_date(normalized)
        installment_total = self._extract_installments(normalized)
        bill_ids = self._create_transaction(
            current_user=current_user,
            db=db,
            amount=amount,
            due_date=due_date,
            transaction_type=transaction_type,
            category=category or "outras",
            issuer=issuer,
            installment_total=installment_total,
            status=status,
        )
        cache_service.invalidate_user_cache(str(current_user.id))

        label = "receita" if transaction_type == BillType.INCOME else "despesa"
        if installment_total and installment_total > 1:
            return LocalChatResult(
                response=(
                    f"{installment_total} parcelas de {label} criadas com sucesso. "
                    f"Valor total: R$ {amount:.2f}."
                ),
                action="income_created" if transaction_type == BillType.INCOME else "expense_created",
                bill_id=bill_ids[0] if bill_ids else None,
            )

        return LocalChatResult(
            response=self._format_created_response(label, amount, category or "outras", issuer, due_date, installment_total, status),
            action="income_created" if transaction_type == BillType.INCOME else "expense_created",
            bill_id=bill_ids[0] if bill_ids else None,
        )

    def _try_pending_transaction_followup(
        self,
        normalized: str,
        original_message: str,
        current_user: User,
        db: Session,
        conversation_history: List[Dict[str, Any]],
    ) -> Optional[LocalChatResult]:
        if not conversation_history:
            return None
        if self._detect_static_intent(normalized) or self._detect_financial_intent(normalized):
            return None

        last_bot_text = ""
        for item in reversed(conversation_history[-6:]):
            if item.get("sender") == "bot":
                last_bot_text = cache_service.normalize_message(str(item.get("text") or ""))
                break
        if not any(marker in last_bot_text for marker in ["me diga com o que", "onde foi", "de onde veio", "faltou"]):
            return None

        pending_message = None
        for item in reversed(conversation_history[-8:]):
            if item.get("sender") != "user":
                continue
            text = str(item.get("text") or "")
            normalized_text = cache_service.normalize_message(text)
            if self._extract_amount(normalized_text) is not None and (
                any(keyword in normalized_text for keyword in self.EXPENSE_KEYWORDS)
                or any(keyword in normalized_text for keyword in self.INCOME_KEYWORDS)
            ):
                pending_message = normalized_text
                break
        if not pending_message:
            return None

        amount = self._extract_amount(pending_message)
        if amount is None:
            return None

        is_income = any(keyword in pending_message for keyword in self.INCOME_KEYWORDS)
        is_expense = any(keyword in pending_message for keyword in self.EXPENSE_KEYWORDS)
        transaction_type = BillType.INCOME if is_income and not is_expense else BillType.EXPENSE
        combined = f"{pending_message} {normalized}"
        category = self._detect_category(combined, transaction_type)
        issuer = self._extract_issuer(normalized, transaction_type) or self._extract_issuer(combined, transaction_type)
        status = self._detect_status(combined)

        if transaction_type == BillType.EXPENSE and ("boleto" in combined or "conta" in combined) and status == BillStatus.PAID:
            category = category or "servicos"
            issuer = issuer or ("Boleto pago" if "boleto" in combined else "Conta paga")

        if transaction_type == BillType.EXPENSE and not category and not issuer:
            return LocalChatResult(
                response=(
                    "Ainda falta entender o tipo do gasto. Pode responder com algo como "
                    "'mercado', 'Uber', 'energia', 'farmácia' ou o nome do lugar."
                ),
                action="ask_for_info",
            )
        if transaction_type == BillType.INCOME and not category and not issuer:
            return LocalChatResult(
                response="Ainda falta a origem da receita. Foi salário, freelance, venda, reembolso ou outra fonte?",
                action="ask_for_info",
            )

        if transaction_type == BillType.INCOME and not category:
            category = "outras"

        due_date = self._extract_date(combined)
        installment_total = self._extract_installments(combined)
        bill_ids = self._create_transaction(
            current_user=current_user,
            db=db,
            amount=amount,
            due_date=due_date,
            transaction_type=transaction_type,
            category=category or "outras",
            issuer=issuer,
            installment_total=installment_total,
            status=status,
        )
        cache_service.invalidate_user_cache(str(current_user.id))

        label = "receita" if transaction_type == BillType.INCOME else "despesa"
        return LocalChatResult(
            response=self._format_created_response(label, amount, category or "outras", issuer, due_date, installment_total, status),
            action="income_created" if transaction_type == BillType.INCOME else "expense_created",
            bill_id=bill_ids[0] if bill_ids else None,
        )

    def _extract_amount(self, normalized: str) -> Optional[float]:
        match = re.search(r"(?:r\$\s*)?(\d{1,3}(?:\.\d{3})*,\d{2}|\d+[,.]\d{1,2}|\d+)\s*(?:reais|real)?", normalized)
        if not match:
            return None
        amount_text = match.group(1)
        if "," in amount_text:
            amount_text = amount_text.replace(".", "").replace(",", ".")
        try:
            amount = float(amount_text)
            return amount if amount > 0 else None
        except ValueError:
            return None

    def _detect_category(self, normalized: str, transaction_type: BillType) -> Optional[str]:
        if transaction_type == BillType.INCOME:
            return "investimentos" if any(self._has_keyword(normalized, k) for k in self.CATEGORY_KEYWORDS["investimentos"]) else None
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if category == "investimentos":
                continue
            if any(self._has_keyword(normalized, keyword) for keyword in keywords):
                return category
        return None

    def _has_keyword(self, normalized: str, keyword: str) -> bool:
        return bool(re.search(rf"\b{re.escape(keyword)}\b", normalized))

    def _extract_issuer(self, normalized: str, transaction_type: BillType) -> Optional[str]:
        patterns = [r"\b(?:no|na|em|de|do|da|para|com)\s+([a-z0-9 ]{2,40})$"]
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                issuer = self._cleanup_issuer(match.group(1))
                if issuer:
                    return issuer.title()

        subject = self._extract_transaction_subject(normalized)
        if subject:
            return subject.title()
        return None

    def _detect_status(self, normalized: str) -> BillStatus:
        if any(self._has_keyword(normalized, keyword) for keyword in ["pago", "paga", "paguei", "quitei"]):
            return BillStatus.PAID
        if any(self._has_keyword(normalized, keyword) for keyword in ["pendente", "aberto", "vencer", "vence"]):
            return BillStatus.PENDING
        return BillStatus.CONFIRMED

    def _extract_transaction_subject(self, normalized: str) -> Optional[str]:
        text = re.sub(r"(?:r\$\s*)?(\d{1,3}(?:\.\d{3})*,\d{2}|\d+[,.]\d{1,2}|\d+)\s*(?:reais|real)?", " ", normalized)
        text = re.sub(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b", " ", text)
        text = re.sub(r"\b\d{1,2}\s*(?:x|vezes|parcelas?)\b", " ", text)
        words = [word for word in re.findall(r"[a-z0-9]+", text) if word not in self.FILLER_WORDS]
        if not words:
            return None
        subject = " ".join(words[:5]).strip()
        return self._cleanup_issuer(subject)

    def _cleanup_issuer(self, issuer: str) -> Optional[str]:
        issuer = re.sub(r"\b(hoje|amanha|ontem|parcelado|parcelas?|vezes|x|reais|real)\b", " ", issuer)
        issuer = re.sub(r"\s+", " ", issuer).strip()
        if not issuer:
            return None
        if issuer in {"gasto", "despesa", "receita", "pagamento", "compra"}:
            return None
        return issuer

    def _format_created_response(
        self,
        label: str,
        amount: float,
        category: str,
        issuer: Optional[str],
        due_date: date,
        installment_total: Optional[int] = None,
        status: BillStatus = BillStatus.CONFIRMED,
    ) -> str:
        issuer_text = f" em {issuer}" if issuer else ""
        category_text = f"Categoria: {self._format_category_label(category)}."
        date_text = f"Data: {due_date.strftime('%d/%m/%Y')}."
        status_text = " Marcada como paga." if status == BillStatus.PAID else ""
        if installment_total and installment_total > 1:
            return (
                f"{installment_total} parcelas de {label}{issuer_text} criadas com sucesso. "
                f"Valor total: R$ {amount:.2f}. {category_text} {date_text}{status_text}"
            )
        return (
            f"{label.capitalize()}{issuer_text} criada com sucesso no valor de R$ {amount:.2f}. "
            f"{category_text} {date_text}{status_text}"
        )

    def _extract_date(self, normalized: str) -> date:
        today = date.today()
        if "amanha" in normalized:
            return today + timedelta(days=1)
        if "ontem" in normalized:
            return today
        match = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", normalized)
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3) or today.year)
            if year < 100:
                year += 2000
            try:
                parsed = date(year, month, day)
                return parsed if parsed >= today else today
            except ValueError:
                return today
        return today

    def _extract_installments(self, normalized: str) -> Optional[int]:
        match = re.search(r"\b(\d{1,2})\s*(?:x|vezes|parcelas?)\b", normalized)
        if not match:
            return None
        total = int(match.group(1))
        return total if total > 1 else None

    def _format_month_label(self, value: date) -> str:
        month_names = [
            "janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
        ]
        return f"{month_names[value.month - 1].capitalize()} de {value.year}"

    def _format_category_label(self, category: str) -> str:
        labels = {
            "alimentacao": "Alimentação",
            "moradia": "Moradia",
            "servicos": "Serviços",
            "transporte": "Transporte",
            "saude": "Saúde",
            "vestuario": "Vestuário",
            "compras": "Compras",
            "lazer": "Lazer",
            "educacao": "Educação",
            "investimentos": "Investimentos",
            "outras": "Outras",
        }
        return labels.get(category, category.capitalize())

    def _create_transaction(
        self,
        current_user: User,
        db: Session,
        amount: float,
        due_date: date,
        transaction_type: BillType,
        category: str,
        issuer: Optional[str],
        installment_total: Optional[int] = None,
        status: BillStatus = BillStatus.CONFIRMED,
    ) -> List[str]:
        total = installment_total or 1
        installment_amount = round(amount / total, 2)
        bill_ids: List[str] = []

        for index in range(total):
            current_amount = installment_amount
            if total > 1 and index == total - 1:
                current_amount = round(amount - installment_amount * (total - 1), 2)
            bill = Bill(
                id=uuid.uuid4(),
                user_id=current_user.id,
                issuer=issuer or ("Receita Manual" if transaction_type == BillType.INCOME else "Despesa Manual"),
                amount=current_amount,
                currency="BRL",
                due_date=due_date + relativedelta(months=index),
                status=status,
                confidence=0.95,
                category=category,
                type=transaction_type,
                is_bill=False,
            )
            db.add(bill)
            bill_ids.append(str(bill.id))

        db.commit()
        return bill_ids


local_chatbot_service = LocalChatbotService()
