import re
from enum import Enum

from app.services.financial_chat_parser import norm


class Intent(str, Enum):
    CANCEL = "cancel"
    CONFIRM = "confirm"
    CORRECT = "correct"
    SIMULATE = "simulate"
    COMPARE = "compare"
    CONSULT = "consult"
    PAY = "pay"
    EDIT = "edit"
    DELETE = "delete"
    HELP = "help"
    REGISTER = "register"


CONFIRM = {
    "sim", "confirmar", "confirmo", "confirmar lancamentos", "pode salvar", "salvar",
    "pode cadastrar", "pode registrar", "sim pode salvar", "pode colocar tudo", "confirma tudo",
}
CANCEL = {"cancelar", "cancela", "nao", "descartar", "cancelar lancamentos", "limpar rascunho"}
BILL_ID = re.compile(r"\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b")
QUESTION = re.compile(
    r"^(?:quanto|quanta|quais|qual|como|quando|mostr[ae]|listar|resumo|me (?:mostre|diga)|"
    r"e (?:no|em|mes)|saldo|gastos por categoria|contas pendentes|planejamento mensal|"
    r"meu planejamento|meu custo de vida)\b"
)


def classify(message):
    n = norm(message).strip().strip(".!?")
    if n in CONFIRM:
        return Intent.CONFIRM
    if n in CANCEL:
        return Intent.CANCEL
    if re.search(r"^se\b|^(?:consigo|posso) (?:comprar|gastar)|\bsimul(?:ar|acao|e)\b", n):
        return Intent.SIMULATE
    if re.search(r"^compar(?:e|ar)|\b(?:em relacao|comparad[oa]|comparacao)\b", n):
        return Intent.COMPARE
    if QUESTION.search(n) or ("?" in message and "\n" not in message):
        return Intent.CONSULT
    if re.match(r"^(?:na verdade|corrija|corrige|corrigir|esse pagamento foi|foi ontem|foi hoje|registra isso|mude o item|troque o item)\b", n):
        return Intent.CORRECT
    if re.match(r"^(?:exclu[ai]|excluir|apagu?e|apagar|remova|remover|delete)\s+", n):
        return Intent.DELETE
    if re.match(r"^(?:edit[ae]|editar|altere|alterar|mude|mudar)\s+", n):
        return Intent.EDIT
    if re.match(r"^(?:marque|marcar|registra|registre|registrar)\b.*\b(?:pago|pagamento)", n):
        return Intent.PAY
    if re.match(r"^(?:paguei|pagamento de)\s+", n) and (
        BILL_ID.search(n) or re.match(r"^(?:paguei|pagamento de)\s+(?!r\$|\d)", n)
    ):
        return Intent.PAY
    if n in {"oi", "ola", "bom dia", "boa tarde", "boa noite", "ajuda", "o que voce faz", "o que vc faz"}:
        return Intent.HELP
    return Intent.REGISTER
