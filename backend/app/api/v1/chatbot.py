from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from datetime import date, datetime
from dateutil.relativedelta import relativedelta  # type: ignore
import uuid
import logging
import re

from app.db.database import get_db
from app.db.models import User, Bill, BillStatus, BillType
from app.api.dependencies import get_current_user
from app.services.ollama_service import ollama_service
from app.services.gemini_service import get_gemini_service
from app.services.cache_service import cache_service
from app.services.local_chatbot_service import local_chatbot_service
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    conversation_history: Optional[List[Dict]] = None


class ChatResponse(BaseModel):
    response: str
    action: Optional[str] = None
    bill_id: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    chat_data: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat with the AI assistant powered by Gemini (se configurado) ou Ollama.
    Can also create expenses/bills from natural language commands.
    """
    try:
        # Verificar limite de uso do chatbot
        notif_prefs = current_user.notif_prefs or {}
        is_premium = notif_prefs.get("is_premium", False)
        
        # Limites: Free = 25 mensagens/mês, Premium = ilimitado
        FREE_LIMIT = 25
        PREMIUM_LIMIT = 1000  # Praticamente ilimitado
        
        # Obter contador atual e data de reset
        chatbot_messages_this_month = notif_prefs.get("chatbot_messages_this_month", 0)
        chatbot_month_reset_date = notif_prefs.get("chatbot_month_reset_date")
        
        # Verificar se precisa resetar o contador (novo mês)
        today = date.today()
        current_month = today.replace(day=1)  # Primeiro dia do mês atual
        
        if not chatbot_month_reset_date or datetime.fromisoformat(chatbot_month_reset_date).date().replace(day=1) < current_month:
            # Resetar contador para novo mês
            chatbot_messages_this_month = 0
            chatbot_month_reset_date = current_month.isoformat()
            notif_prefs["chatbot_messages_this_month"] = 0
            notif_prefs["chatbot_month_reset_date"] = chatbot_month_reset_date
            current_user.notif_prefs = notif_prefs
            db.commit()
        
        local_result = local_chatbot_service.try_handle(
            message=chat_data.message,
            current_user=current_user,
            db=db,
            conversation_history=chat_data.conversation_history or []
        )
        if local_result:
            return ChatResponse(
                response=local_result.response,
                action=local_result.action,
                bill_id=local_result.bill_id
            )

        if not settings.CHATBOT_AI_ENABLED:
            return ChatResponse(
                response=(
                    "Ainda nao entendi esse pedido no modo economico. "
                    "Tente perguntar sobre pendentes, vencidas, saldo do mes, proximos vencimentos "
                    "ou registrar algo como 'gastei R$ 35 no Uber'."
                ),
                action="chat"
            )

        # Verificar limite apenas quando a chamada realmente vai usar IA.
        limit = PREMIUM_LIMIT if is_premium else FREE_LIMIT
        if chatbot_messages_this_month >= limit:
            remaining_days = (current_month + relativedelta(months=1) - today).days
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Limite de {limit} mensagens do chatbot atingido este mês. {'Faça upgrade para Premium para uso ilimitado.' if not is_premium else 'Limite mensal atingido.'} O limite será resetado em {remaining_days} dia(s)."
            )

        chatbot_messages_this_month += 1
        notif_prefs["chatbot_messages_this_month"] = chatbot_messages_this_month
        current_user.notif_prefs = notif_prefs
        db.commit()
        
        # Verificar se deve usar Gemini ou Ollama
        gemini_service = get_gemini_service()
        ai_service = gemini_service if gemini_service else ollama_service
        
        # Primeiro, tentar extrair informações de criação de transação (despesa ou receita)
        expense_data = await ai_service.extract_expense_from_message(chat_data.message)
        
        # Detectar se é receita ou despesa baseado na mensagem (mais palavras-chave)
        message_lower = chat_data.message.lower().strip()
        is_income = any(keyword in message_lower for keyword in [
            'receita', 'ganho', 'entrada', 'salário', 'renda', 'adicionar em receita',
            'adicionar receita', 'criar receita', 'adicionar como receita', 'sim pode adicionar em receita',
            'adicionar em receita', 'adicionar como receita', 'receita de', 'ganhei', 'encontrei', 'achei',
            'achado', 'dinheiro encontrado', 'dinheiro achado', 'coloca', 'põe', 'adiciona', 'registra'
        ])
        is_expense = any(keyword in message_lower for keyword in [
            'despesa', 'gasto', 'saída', 'boleto', 'conta', 'pagamento', 'adicionar despesa',
            'criar despesa', 'adicionar gasto', 'paguei', 'gastei'
        ])
        
        # Verificar histórico da conversa para detectar confirmações
        conversation_history = chat_data.conversation_history or []
        has_pending_transaction = False
        pending_amount = None
        pending_type = None
        pending_issuer = None
        pending_installment_total = None
        pending_is_installment = False
        
        # Procurar no histórico por menções de valores, tipos, categorias e emissores
        for msg in reversed(conversation_history[-5:]):  # Últimas 5 mensagens
            msg_text = (msg.get('text') or msg.get('message') or '').lower()
            # Procurar por valores (R$ X,XX ou X reais)
            amount_match = re.search(r'r?\$?\s*(\d+[.,]\d{2}|\d+)\s*(reais?)?', msg_text)
            if amount_match:
                amount_str = amount_match.group(1).replace(',', '.')
                try:
                    pending_amount = float(amount_str)
                    # Verificar se menciona receita
                    if any(kw in msg_text for kw in ['receita', 'ganho', 'entrada', 'salário', 'ganhei', 'recebi']):
                        pending_type = BillType.INCOME
                        has_pending_transaction = True
                    # Verificar se menciona despesa
                    elif any(kw in msg_text for kw in ['despesa', 'gasto', 'pago', 'paguei', 'gastei']):
                        pending_type = BillType.EXPENSE
                        has_pending_transaction = True
                    # Se não especificar, verificar contexto atual
                    elif is_income:
                        pending_type = BillType.INCOME
                        has_pending_transaction = True
                    elif is_expense:
                        pending_type = BillType.EXPENSE
                        has_pending_transaction = True
                except:
                    pass
            
            # Procurar por número de parcelas no histórico
            if not pending_installment_total:
                # Padrões: "3x", "6 vezes", "parcelado em 12", "dividido em 4"
                installment_match = re.search(r'(\d+)\s*(x|vezes|parcelas?)', msg_text)
                if installment_match:
                    try:
                        pending_installment_total = int(installment_match.group(1))
                        pending_is_installment = True
                        logger.info(f"📦 Parcelamento detectado no histórico: {pending_installment_total} parcelas")
                    except:
                        pass
            
            # Procurar por categoria no histórico (palavras-chave de categorias)
            if not pending_issuer:  # Só procurar se ainda não tiver emissor
                category_keywords = {
                    'alimentacao': ['comida', 'restaurante', 'supermercado', 'mercado', 'padaria', 'lanche', 'delivery', 'ifood', 'alimentação'],
                    'moradia': ['aluguel', 'condomínio', 'água', 'luz', 'energia', 'gás', 'internet', 'telefone', 'iptu'],
                    'transporte': ['gasolina', 'combustível', 'uber', 'táxi', 'ônibus', 'metrô', 'estacionamento', 'pedágio'],
                    'saude': ['médico', 'remédio', 'farmácia', 'hospital', 'plano de saúde', 'dentista'],
                    'vestuario': ['roupas', 'vestuário', 'calçado', 'sapatos', 'tênis', 'camisa', 'calça', 'blusa'],
                    'compras': ['compras', 'shopping', 'loja', 'adquirir'],
                    'lazer': ['cinema', 'show', 'festa', 'diversão', 'jogos'],
                    'educacao': ['escola', 'curso', 'faculdade', 'universidade', 'livro']
                }
                # Se encontrar palavra-chave de categoria, pode ser o emissor também
                for cat, keywords in category_keywords.items():
                    if any(kw in msg_text for kw in keywords):
                        # Se a mensagem parece ser um nome de estabelecimento, usar como emissor
                        if len(msg_text.split()) <= 3:  # Nomes curtos provavelmente são emissores
                            pending_issuer = msg_text.title()
                        break
            
            # Procurar por emissor (nomes próprios, estabelecimentos)
            if not pending_issuer and len(msg_text.split()) <= 5:
                # Se a mensagem parece ser uma resposta direta (não é pergunta), pode ser emissor
                if not any(q in msg_text for q in ['?', 'qual', 'onde', 'como', 'quando', 'quanto']):
                    # Verificar se tem palavras que indicam estabelecimento
                    if any(word in msg_text for word in ['supermercado', 'loja', 'mercado', 'farmácia', 'restaurante', 'energia', 'água', 'luz']):
                        pending_issuer = msg_text.title()
        
        # Se não detectar explicitamente, assumir despesa (comportamento padrão)
        transaction_type = BillType.INCOME if is_income and not is_expense else BillType.EXPENSE
        if pending_type:
            transaction_type = pending_type
        
        logger.info(f"Chat message: {chat_data.message}")
        logger.info(f"Expense data extracted: {expense_data}")
        logger.info(f"Is income: {is_income}, Is expense: {is_expense}, Transaction type: {transaction_type}")
        logger.info(f"Has pending transaction: {has_pending_transaction}, Amount: {pending_amount}")
        
        # Se detectar confirmação simples ("sim", "pode", "confirma") e houver transação pendente
        is_confirmation = any(word in message_lower for word in ['sim', 'pode', 'confirma', 'ok', 'tudo bem', 'pode adicionar', 'adiciona', 'coloca', 'põe'])
        
        # Verificar se é comando de criação (despesa ou receita) ou se precisa perguntar mais informações
        is_create_command = expense_data and expense_data.get("action") in ["create_expense", "create_income"]
        needs_info = expense_data and expense_data.get("action") == "ask_for_info"
        
        # PRIORIDADE 1: Se o prompt retornou uma ação, usar ela (prompt tem prioridade sobre detecção local)
        if expense_data and expense_data.get("action") == "create_income":
            transaction_type = BillType.INCOME
            is_income = True
            is_expense = False
            logger.info("✅ Prompt retornou create_income - forçando tipo como INCOME")
        elif expense_data and expense_data.get("action") == "create_expense":
            transaction_type = BillType.EXPENSE
            is_income = False
            is_expense = True
            logger.info("✅ Prompt retornou create_expense - forçando tipo como EXPENSE")
        elif needs_info:
            # Determinar tipo baseado na mensagem quando precisa perguntar
            if is_income and not is_expense:
                transaction_type = BillType.INCOME
            elif is_expense and not is_income:
                transaction_type = BillType.EXPENSE
            else:
                # Se não conseguir determinar, assumir despesa (comportamento padrão)
                transaction_type = BillType.EXPENSE
            logger.info(f"❓ Prompt retornou ask_for_info - tipo: {transaction_type.value}, missing: {expense_data.get('missing_info')}")
        
        # Verificar se menciona parcelamento e extrair número de parcelas da mensagem atual
        is_installment_mentioned = any(word in message_lower for word in ['parcelado', 'parcela', 'parcelas', 'vezes', 'dividido'])
        installment_total = None
        
        # Tentar extrair número de parcelas da mensagem atual
        if is_installment_mentioned:
            installment_match = re.search(r'(\d+)\s*(x|vezes|parcelas?)', message_lower)
            if installment_match:
                try:
                    installment_total = int(installment_match.group(1))
                    logger.info(f"📦 Parcelamento detectado: {installment_total} parcelas")
                except:
                    pass
        
        # Se mencionou parcelamento mas não tem o número, perguntar
        if (expense_data and expense_data.get("is_installment") and not expense_data.get("installment_total") and not installment_total) or \
           (is_installment_mentioned and not installment_total and not pending_installment_total):
            amount = expense_data.get("amount") if expense_data else pending_amount
            if amount and amount > 0:
                transaction_label = "receita" if transaction_type == BillType.INCOME else "despesa"
                return ChatResponse(
                    response=f"Entendi! Você {transaction_label} R$ {amount:.2f} parcelado. Em quantas vezes foi parcelado? (ex: 3x, 6x, 12x)",
                    action="ask_for_info"
                )
        
        # Usar número de parcelas extraído ou do histórico
        final_installment_total = installment_total or pending_installment_total or (expense_data.get("installment_total") if expense_data else None)
        final_is_installment = final_installment_total is not None and final_installment_total > 1
        
        # Se precisa perguntar mais informações, fazer pergunta contextual
        if needs_info:
            amount = expense_data.get("amount") if expense_data else None
            missing_info = expense_data.get("missing_info") if expense_data else None
            transaction_label = "receita" if transaction_type == BillType.INCOME else "despesa"
            
            if not amount or amount <= 0:
                return ChatResponse(
                    response=f"Não consegui identificar o valor da {transaction_label}. Por favor, informe o valor. Exemplo: 'Adicionar {transaction_label} de R$ 150,50'",
                    action="ask_for_info"
                )
            
            # Perguntas contextuais baseadas no que falta
            if transaction_type == BillType.INCOME:
                # Para receitas, sempre perguntar sobre a origem/fonte
                if missing_info == "category" or missing_info == "category_and_issuer" or not missing_info:
                    return ChatResponse(
                        response=f"Entendi! Você recebeu R$ {amount:.2f}. De onde veio essa receita? (ex: salário, freelance, vendas, comissão, bônus, reembolso, aluguel recebido, investimentos, outras)",
                        action="ask_for_info"
                    )
                elif missing_info == "issuer":
                    category_text = expense_data.get("category", "essa receita")
                    return ChatResponse(
                        response=f"Entendi! Você recebeu R$ {amount:.2f} de {category_text}. Qual foi a fonte/origem dessa receita? (ex: Empresa X, Cliente Y, Banco Z)",
                        action="ask_for_info"
                    )
            else:
                # Para despesas
                if missing_info == "category_and_issuer":
                    return ChatResponse(
                        response=f"Entendi! Você {transaction_label} R$ {amount:.2f}. Para organizar melhor, me diga:\n\n• Com o que foi esse gasto? (ex: compras, roupas, energia, alimentação)\n• Onde foi? (ex: Supermercado X, Loja Y, Energia Elétrica)",
                        action="ask_for_info"
                    )
                elif missing_info == "category":
                    issuer_text = expense_data.get("issuer", "esse gasto")
                    return ChatResponse(
                        response=f"Entendi! Você {transaction_label} R$ {amount:.2f} em {issuer_text}. Em qual categoria devo classificar? (ex: compras, roupas, energia, alimentação, transporte, saúde, lazer, educação, outras)",
                        action="ask_for_info"
                    )
                elif missing_info == "issuer":
                    category_text = expense_data.get("category", "essa categoria")
                    return ChatResponse(
                        response=f"Entendi! Você {transaction_label} R$ {amount:.2f} na categoria {category_text}. Onde foi esse gasto? (ex: Supermercado X, Loja Y, Energia Elétrica, Uber)",
                        action="ask_for_info"
                    )
                else:
                    return ChatResponse(
                        response=f"Entendi! Você {transaction_label} R$ {amount:.2f}. Pode me dar mais detalhes sobre esse gasto? (categoria, onde foi, etc.)",
                        action="ask_for_info"
                    )
        
        # Verificar se é resposta a uma pergunta anterior (tem valor pendente e nova informação)
        is_followup_response = (pending_amount and 
                               (expense_data and expense_data.get("category") or 
                                expense_data and expense_data.get("issuer") or
                                any(cat in message_lower for cat in ['compras', 'roupas', 'energia', 'alimentação', 'transporte', 'saúde', 'lazer', 'educação'])))
        
        if is_create_command or (is_confirmation and has_pending_transaction and pending_amount) or is_followup_response:
            # Criar transação (despesa ou receita)
            try:
                # Usar valor do expense_data ou do histórico
                amount = None
                if expense_data and expense_data.get("amount"):
                    amount = expense_data.get("amount")
                elif pending_amount:
                    amount = pending_amount
                
                # Validar dados mínimos
                if not amount or amount <= 0:
                    transaction_label = "receita" if transaction_type == BillType.INCOME else "despesa"
                    return ChatResponse(
                        response=f"Não consegui identificar o valor da {transaction_label}. Por favor, informe o valor. Exemplo: 'Adicionar {transaction_label} de R$ 150,50'",
                        action="error"
                    )
                
                # Processar data de vencimento
                due_date = date.today()
                if expense_data and expense_data.get("due_date"):
                    try:
                        # Tentar parsear a data
                        if isinstance(expense_data["due_date"], str):
                            parsed_date = datetime.fromisoformat(expense_data["due_date"]).date()
                            # Se a data for no passado, usar hoje como base
                            if parsed_date < date.today():
                                due_date = date.today()
                            else:
                                due_date = parsed_date
                        else:
                            due_date = date.today()
                    except:
                        due_date = date.today()
                
                # Determinar issuer baseado no tipo e histórico (priorizar expense_data, depois histórico, depois padrão)
                if expense_data and expense_data.get("issuer"):
                    default_issuer = expense_data.get("issuer")
                elif pending_issuer:
                    default_issuer = pending_issuer
                elif is_followup_response and message_lower:
                    # Se é resposta a pergunta, tentar extrair emissor da mensagem atual
                    # Procurar por nomes de estabelecimentos na mensagem
                    words = message_lower.split()
                    if len(words) <= 5:  # Mensagens curtas provavelmente são nomes
                        default_issuer = message_lower.title()
                    else:
                        default_issuer = "Despesa Manual" if transaction_type == BillType.EXPENSE else "Receita Manual"
                elif transaction_type == BillType.INCOME:
                    default_issuer = "Receita Manual"
                else:
                    default_issuer = "Despesa Manual"
                
                # Criar transação (não é boleto, é transação manual)
                # Usar o amount calculado (pode vir de expense_data ou pending_amount)
                final_amount = amount if amount else (expense_data.get("amount") if expense_data else 0)
                
                # Extrair categoria do expense_data, mensagem atual ou usar padrão
                final_category = None
                if expense_data and expense_data.get("category"):
                    final_category = expense_data.get("category")
                elif is_followup_response:
                    # Se é resposta a pergunta, tentar extrair categoria da mensagem atual
                    if transaction_type == BillType.INCOME:
                        # Categorias para receitas - mapear palavras-chave para categorias
                        income_category_map = {
                            'salário': 'investimentos',
                            'salario': 'investimentos',
                            'sal': 'investimentos',
                            'freelance': 'investimentos',
                            'freela': 'investimentos',
                            'vendas': 'investimentos',
                            'venda': 'investimentos',
                            'comissão': 'investimentos',
                            'comissao': 'investimentos',
                            'bonus': 'investimentos',
                            'bônus': 'investimentos',
                            'renda': 'investimentos',
                            'dividendos': 'investimentos',
                            'juros': 'investimentos',
                            'aplicação': 'investimentos',
                            'aplicacao': 'investimentos',
                            'poupança': 'investimentos',
                            'poupanca': 'investimentos',
                            'ações': 'investimentos',
                            'acoes': 'investimentos',
                            'investimento': 'investimentos',
                            'reembolso': 'investimentos',
                            'aluguel recebido': 'investimentos',
                            'aluguel': 'investimentos',
                            'outras': 'outras'
                        }
                        for keyword, category in income_category_map.items():
                            if keyword in message_lower:
                                final_category = category
                                break
                        # Se não encontrar categoria, NÃO criar - deve perguntar novamente
                        if not final_category:
                            return ChatResponse(
                                response=f"Entendi! Você recebeu R$ {final_amount:.2f}. De onde veio essa receita? (ex: salário, freelance, vendas, comissão, bônus, reembolso, aluguel recebido, investimentos, outras)",
                                action="ask_for_info"
                            )
                    else:
                        # Categorias para despesas
                        category_map = {
                            'compras': 'compras',
                            'compra': 'compras',
                            'shopping': 'compras',
                            'roupas': 'vestuario',
                            'roupa': 'vestuario',
                            'vestuário': 'vestuario',
                            'energia': 'moradia',
                            'luz': 'moradia',
                            'água': 'moradia',
                            'alimentação': 'alimentacao',
                            'comida': 'alimentacao',
                            'restaurante': 'alimentacao',
                            'transporte': 'transporte',
                            'uber': 'transporte',
                            'saúde': 'saude',
                            'médico': 'saude',
                            'lazer': 'lazer',
                            'educação': 'educacao',
                            'educacao': 'educacao'
                        }
                        for keyword, category in category_map.items():
                            if keyword in message_lower:
                                final_category = category
                                break
                        if not final_category:
                            final_category = "outras"
                elif transaction_type == BillType.INCOME:
                    # Para receitas SEM categoria, SEMPRE perguntar - NÃO aceitar sem categoria
                    return ChatResponse(
                        response=f"Entendi! Você recebeu R$ {final_amount:.2f}. De onde veio essa receita? (ex: salário, freelance, vendas, comissão, bônus, reembolso, aluguel recebido, investimentos, outras)",
                        action="ask_for_info"
                    )
                
                # VALIDAÇÃO CRÍTICA: Receitas SEMPRE precisam de categoria - não aceitar sem categoria
                if transaction_type == BillType.INCOME and not final_category:
                    return ChatResponse(
                        response=f"Entendi! Você recebeu R$ {final_amount:.2f}. De onde veio essa receita? (ex: salário, freelance, vendas, comissão, bônus, reembolso, aluguel recebido, investimentos, outras)",
                        action="ask_for_info"
                    )
                
                # Se for parcelamento, criar múltiplas transações
                if final_is_installment and final_installment_total and final_installment_total > 1:
                    # Calcular valor de cada parcela (arredondar para 2 casas decimais)
                    installment_amount = round(final_amount / final_installment_total, 2)
                    
                    # Ajustar última parcela para compensar arredondamentos
                    total_installments = installment_amount * (final_installment_total - 1)
                    last_installment_amount = round(final_amount - total_installments, 2)
                    
                    # Criar todas as parcelas
                    created_bills = []
                    for i in range(1, final_installment_total + 1):
                        # Calcular data de vencimento (primeira parcela na data informada, demais a cada mês)
                        if i == 1:
                            installment_due_date = due_date
                        else:
                            # Adicionar (i-1) meses à data inicial
                            installment_due_date = due_date + relativedelta(months=(i-1))
                        
                        # Usar valor ajustado na última parcela
                        current_amount = last_installment_amount if i == final_installment_total else installment_amount
                        
                        bill = Bill(
                            id=uuid.uuid4(),
                            user_id=current_user.id,
                            issuer=default_issuer,
                            amount=current_amount,
                            currency="BRL",
                            due_date=installment_due_date,
                            status=BillStatus.CONFIRMED,
                            confidence=0.9,
                            category=final_category,
                            type=transaction_type,
                            is_bill=False
                        )
                        
                        db.add(bill)
                        created_bills.append(bill)
                    
                    db.commit()
                    for bill in created_bills:
                        db.refresh(bill)
                    
                    logger.info(f"✅ {final_installment_total} parcelas criadas no banco: Total R$ {final_amount:.2f}, Valor por parcela R$ {installment_amount:.2f}")
                    
                    # Preparar resposta
                    transaction_label = "receita" if transaction_type == BillType.INCOME else "despesa"
                    issuer_text = f" de {default_issuer}" if default_issuer not in ["Receita Manual", "Despesa Manual"] else ""
                    
                    first_due = created_bills[0].due_date.strftime('%d/%m/%Y')
                    last_due = created_bills[-1].due_date.strftime('%d/%m/%Y')
                    
                    response_text = f"✅ {final_installment_total} parcelas de {transaction_label}{issuer_text} criadas com sucesso!\n\n"
                    response_text += f"💰 Valor total: R$ {final_amount:.2f}\n"
                    response_text += f"💵 Valor por parcela: R$ {installment_amount:.2f}\n"
                    response_text += f"📅 Primeira parcela: {first_due}\n"
                    response_text += f"📅 Última parcela: {last_due}"
                    
                    action_name = "income_created" if transaction_type == BillType.INCOME else "expense_created"
                else:
                    # Criar transação única (não parcelada)
                    bill = Bill(
                        id=uuid.uuid4(),
                        user_id=current_user.id,
                        issuer=default_issuer,
                        amount=float(final_amount),
                        currency="BRL",
                        due_date=due_date,
                        status=BillStatus.CONFIRMED,
                        confidence=0.9,
                        category=final_category,
                        type=transaction_type,  # EXPENSE ou INCOME
                        is_bill=False  # Transação manual, não é boleto
                    )
                    
                    db.add(bill)
                    db.commit()
                    db.refresh(bill)
                    
                    logger.info(f"✅ Transação criada no banco: ID={bill.id}, Type={bill.type.value}, Amount={bill.amount}, IsBill={bill.is_bill}, Status={bill.status.value}")
                    
                    # Preparar resposta
                    transaction_label = "receita" if transaction_type == BillType.INCOME else "despesa"
                    issuer_text = f" de {bill.issuer}" if bill.issuer not in ["Receita Manual", "Despesa Manual"] else ""
                    date_text = f" com vencimento em {bill.due_date.strftime('%d/%m/%Y')}" if bill.due_date else ""
                    
                    response_text = f"✅ {transaction_label.capitalize()} criada com sucesso!{issuer_text} no valor de R$ {bill.amount:.2f}{date_text}."
                    
                    action_name = "income_created" if transaction_type == BillType.INCOME else "expense_created"
                
                logger.info(f"Retornando action: {action_name}, bill_id: {bill.id}")
                
                return ChatResponse(
                    response=response_text,
                    action=action_name,
                    bill_id=str(bill.id)
                )
                
            except Exception as e:
                logger.error(f"Error creating transaction from chat: {e}")
                transaction_label = "receita" if transaction_type == BillType.INCOME else "despesa"
                return ChatResponse(
                    response=f"Desculpe, ocorreu um erro ao criar a {transaction_label}: {str(e)}",
                    action="error"
                )
        
        # Se não for comando de criação, processar como chat normal
        # Verificar cache primeiro (apenas para mensagens simples ou sem contexto crítico)
        message_lower = chat_data.message.lower().strip()
        is_simple_query = cache_service._is_simple_message(chat_data.message)
        
        # Para mensagens simples, tentar cache antes de buscar dados
        if is_simple_query:
            cached_response = cache_service.get_cached_response(str(current_user.id), chat_data.message)
            if cached_response:
                logger.info(f"Cache hit for simple message from user {current_user.id}")
                return ChatResponse(response=cached_response, action="chat")
        
        user_bills = db.query(Bill).filter(Bill.user_id == current_user.id).all()
        
        pending_bills = [b for b in user_bills if b.status in [BillStatus.PENDING, BillStatus.CONFIRMED]]
        confirmed_bills = [b for b in user_bills if b.status == BillStatus.CONFIRMED]
        scheduled_bills = [b for b in user_bills if b.status == BillStatus.SCHEDULED]
        paid_bills = [b for b in user_bills if b.status == BillStatus.PAID]
        
        today = date.today()
        overdue_bills = [b for b in user_bills if b.due_date and b.due_date < today and b.status != BillStatus.PAID]
        
        total_pending = sum(b.amount for b in pending_bills if b.amount) or 0.0
        total_paid = sum(b.amount for b in paid_bills if b.amount) or 0.0
        
        # Calcular receitas e despesas do mês atual
        current_month = today.month
        current_year = today.year
        monthly_expenses = sum(
            b.amount for b in user_bills 
            if b.due_date and b.due_date.month == current_month and b.due_date.year == current_year
            and b.type == BillType.EXPENSE and b.status in [BillStatus.PAID, BillStatus.CONFIRMED]
        ) or 0.0
        monthly_income = sum(
            b.amount for b in user_bills 
            if b.due_date and b.due_date.month == current_month and b.due_date.year == current_year
            and b.type == BillType.INCOME and b.status in [BillStatus.PAID, BillStatus.CONFIRMED]
        ) or 0.0
        monthly_balance = monthly_income - monthly_expenses
        
        # Agrupar por categoria com detalhes
        categories = {}
        for bill in user_bills:
            cat = bill.category or "outras"
            if cat not in categories:
                categories[cat] = {"total": 0.0, "count": 0, "bills": []}
            categories[cat]["total"] += (bill.amount or 0)
            categories[cat]["count"] += 1
            if len(categories[cat]["bills"]) < 5:  # Limitar a 5 boletos por categoria
                categories[cat]["bills"].append({
                    "issuer": bill.issuer,
                    "amount": bill.amount,
                    "due_date": bill.due_date.isoformat() if bill.due_date else None,
                    "status": bill.status.value
                })
        
        # Top emissores com detalhes
        issuers = {}
        for bill in user_bills:
            issuer = bill.issuer or "Desconhecido"
            if issuer not in issuers:
                issuers[issuer] = {"total": 0.0, "count": 0, "bills": []}
            issuers[issuer]["total"] += (bill.amount or 0)
            issuers[issuer]["count"] += 1
            if len(issuers[issuer]["bills"]) < 3:  # Limitar a 3 boletos por emissor
                issuers[issuer]["bills"].append({
                    "amount": bill.amount,
                    "due_date": bill.due_date.isoformat() if bill.due_date else None,
                    "status": bill.status.value,
                    "category": bill.category
                })
        
        # Lista detalhada de boletos pendentes (próximos 10)
        next_bills = sorted(
            [b for b in pending_bills if b.due_date],
            key=lambda x: x.due_date or date.max
        )[:10]
        
        # Lista detalhada de boletos vencidos
        overdue_details = [
            {
                "issuer": b.issuer,
                "amount": b.amount,
                "due_date": b.due_date.isoformat() if b.due_date else None,
                "days_overdue": (today - b.due_date).days if b.due_date else 0
            }
            for b in overdue_bills
        ]
        
        context = {
            "user_name": current_user.name,
            "total_bills": len(user_bills),
            "pending_bills": len(pending_bills),
            "confirmed_bills": len(confirmed_bills),
            "scheduled_bills": len(scheduled_bills),
            "paid_bills": len(paid_bills),
            "overdue_bills": len(overdue_bills),
            "total_pending": total_pending,
            "total_paid": total_paid,
            "monthly_expenses": monthly_expenses,
            "monthly_income": monthly_income,
            "monthly_balance": monthly_balance,
            "current_month": f"{current_month}/{current_year}",
            "categories": categories,
            "top_issuers": dict(sorted(issuers.items(), key=lambda x: x[1]["total"], reverse=True)[:5]),
            "next_bills": [
                {
                    "issuer": b.issuer,
                    "amount": b.amount,
                    "due_date": b.due_date.isoformat() if b.due_date else None,
                    "days_until": (b.due_date - today).days if b.due_date else None,
                    "category": b.category
                }
                for b in next_bills
            ],
            "overdue_details": overdue_details,
        }
        
        # Verificar cache com contexto (para mensagens mais complexas)
        if not is_simple_query:
            context_hash = cache_service.get_context_hash(context)
            cached_response = cache_service.get_cached_response(
                str(current_user.id), 
                chat_data.message, 
                context_hash
            )
            if cached_response:
                logger.info(f"Cache hit for contextual message from user {current_user.id}")
                return ChatResponse(response=cached_response, action="chat")
        
        # Chamar AI service (Gemini ou Ollama) para gerar resposta
        try:
            response_text = await ai_service.chat(
                message=chat_data.message,
                context=context,
                conversation_history=chat_data.conversation_history or []
            )
            
            # Cachear a resposta apenas se não for erro
            if response_text and not response_text.startswith("⚠️") and not response_text.startswith("❌"):
                if is_simple_query:
                    # Mensagens simples: cache por 1 hora
                    cache_service.set_cached_response(
                        str(current_user.id),
                        chat_data.message,
                        response_text,
                        ttl=3600
                    )
                else:
                    # Mensagens contextuais: cache por 5 minutos com hash do contexto
                    context_hash = cache_service.get_context_hash(context)
                    cache_service.set_cached_response(
                        str(current_user.id),
                        chat_data.message,
                        response_text,
                        context_hash=context_hash,
                        ttl=300
                    )
        except Exception as ai_error:
            logger.error(f"AI service error ({'Gemini' if gemini_service else 'Ollama'}): {ai_error}", exc_info=True)
            
            # Mensagem de erro mais específica baseada no tipo de erro
            error_str = str(ai_error).lower()
            service_name = "Gemini" if gemini_service else "Ollama"
            
            # Extrair mensagem de erro específica se disponível
            error_message = str(ai_error)
            
            if gemini_service:
                # Erros específicos do Gemini
                if "api_key" in error_str or "invalid api key" in error_str or "authentication" in error_str:
                    response_text = f"""⚠️ **Erro de autenticação com {service_name}**

**Problema:** A chave da API do Google não está configurada corretamente.

**Para resolver:**
1. Acesse o Railway Dashboard → Variables
2. Verifique se `GEMINI_API_KEY` está configurada
3. Verifique se a chave está correta (obtenha em: https://aistudio.google.com/apikey)
4. Se necessário, adicione `USE_GEMINI=true` nas variáveis

**Enquanto isso, você pode:**
📄 Registrar gastos pela tela Adicionar ou pelo chat
📊 Visualizar seu dashboard
🔔 Configurar lembretes
💰 Adicionar despesas via formulário"""
                elif "quota" in error_str or "limit" in error_str or "rate limit" in error_str:
                    response_text = f"""⚠️ **Limite da API do Google excedido**

**Problema:** Você atingiu o limite de requisições da API do Gemini.

**Para resolver:**
1. Aguarde alguns minutos e tente novamente
2. Verifique seus limites em: https://aistudio.google.com/apikey
3. Considere fazer upgrade do plano da API do Google

**Enquanto isso, você pode:**
📄 Registrar gastos pela tela Adicionar ou pelo chat
📊 Visualizar seu dashboard
🔔 Configurar lembretes
💰 Adicionar despesas via formulário"""
                elif "timeout" in error_str or "timed out" in error_str:
                    response_text = f"""⚠️ **Timeout ao conectar com {service_name}**

**Problema:** A conexão com a API do Google está demorando muito.

**Para resolver:**
1. Verifique sua conexão com a internet
2. Aguarde alguns segundos e tente novamente
3. Verifique se há problemas com a API do Google

**Enquanto isso, você pode:**
📄 Registrar gastos pela tela Adicionar ou pelo chat
📊 Visualizar seu dashboard
🔔 Configurar lembretes
💰 Adicionar despesas via formulário"""
                elif "model" in error_str or "not found" in error_str:
                    response_text = f"""⚠️ **Modelo do {service_name} não encontrado**

**Problema:** O modelo configurado não está disponível.

**Para resolver:**
1. Verifique a variável `GEMINI_MODEL` no Railway
2. Use um modelo válido como: `gemini-2.0-flash` ou `gemini-1.5-pro`
3. Verifique modelos disponíveis em: https://aistudio.google.com/apikey

**Enquanto isso, você pode:**
📄 Registrar gastos pela tela Adicionar ou pelo chat
📊 Visualizar seu dashboard
🔔 Configurar lembretes
💰 Adicionar despesas via formulário"""
                elif "connect" in error_str or "connection" in error_str or "network" in error_str:
                    response_text = f"""⚠️ **Erro de conexão com {service_name}**

**Problema:** Não foi possível conectar com a API do Google.

**Para resolver:**
1. Verifique sua conexão com a internet
2. Verifique se a `GEMINI_API_KEY` está correta no Railway
3. Verifique os limites da API do Google
4. Tente novamente em alguns instantes

**Enquanto isso, você pode:**
📄 Registrar gastos pela tela Adicionar ou pelo chat
📊 Visualizar seu dashboard
🔔 Configurar lembretes
💰 Adicionar despesas via formulário"""
                else:
                    # Mensagem genérica mas com a mensagem de erro específica
                    response_text = f"""⚠️ **Erro ao conectar com {service_name}**

**Detalhes:** {error_message}

**Para resolver:**
1. Verifique se a `GEMINI_API_KEY` está correta no Railway
2. Verifique sua conexão com a internet
3. Verifique os limites da API do Google
4. Tente novamente em alguns instantes

**Enquanto isso, você pode:**
📄 Registrar gastos pela tela Adicionar ou pelo chat
📊 Visualizar seu dashboard
🔔 Configurar lembretes
💰 Adicionar despesas via formulário"""
            else:
                # Erros do Ollama
                if "timeout" in error_str:
                    response_text = """⏱️ O servidor de IA está demorando para responder.

Mas posso ajudá-lo com informações rápidas:

📄 **Adicionar**: registre gastos pela tela Adicionar ou pelo chat
📊 **Dashboard**: Veja seus gastos e receitas
🔔 **Lembretes**: Configure notificações antes dos vencimentos
🤖 **Adicionar Despesa**: Digite "Adicionar despesa de R$ 150,50 para energia"

Tente novamente em alguns instantes ou use as funcionalidades do menu."""
                else:
                    response_text = f"""⚠️ O servidor de IA ({service_name}) não está disponível.

**Para resolver:**
1. Verifique se o Ollama está rodando na porta 11434
2. Se não estiver, instale e inicie o Ollama
3. Baixe o modelo: `ollama pull llama3.2`

**Enquanto isso, você pode:**
📄 Registrar gastos pela tela Adicionar ou pelo chat
📊 Visualizar seu dashboard
🔔 Configurar lembretes
💰 Adicionar despesas via formulário

Tente novamente após iniciar o Ollama."""
            
            # Garantir que response_text está definido (fallback genérico)
            if 'response_text' not in locals() or not response_text:
                response_text = f"""⚠️ Erro ao conectar com o servidor de IA ({service_name}): {str(ai_error)[:100]}

**O que posso fazer:**
• Ajudar você a entender como usar o sistema
• Explicar funcionalidades do EconomizeIA
• Orientar como registrar gastos manualmente
• Explicar como agendar pagamentos

**Para adicionar despesas via chat:**
Use comandos como:
• "Adicionar despesa de R$ 150,50 para energia elétrica"
• "Registrar R$ 300,00 de energia vencendo em 15/12/2024"

Por favor, verifique a configuração e tente novamente em alguns instantes."""
        
        return ChatResponse(response=response_text, action="chat")
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return ChatResponse(
            response="Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.",
            action="error"
        )

