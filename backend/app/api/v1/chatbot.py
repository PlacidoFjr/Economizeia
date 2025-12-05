from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from datetime import date, datetime
import uuid
import logging

from app.db.database import get_db
from app.db.models import User, Bill, BillStatus, BillType
from app.api.dependencies import get_current_user
from app.services.ollama_service import ollama_service
from app.services.gemini_service import get_gemini_service
from app.services.cache_service import cache_service
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
        
        # Procurar no histórico por menções de valores e tipos
        for msg in reversed(conversation_history[-5:]):  # Últimas 5 mensagens
            msg_text = (msg.get('text') or msg.get('message') or '').lower()
            # Procurar por valores (R$ X,XX ou X reais)
            import re
            amount_match = re.search(r'r?\$?\s*(\d+[.,]\d{2}|\d+)\s*(reais?)?', msg_text)
            if amount_match:
                amount_str = amount_match.group(1).replace(',', '.')
                try:
                    pending_amount = float(amount_str)
                    # Verificar se menciona receita
                    if any(kw in msg_text for kw in ['receita', 'ganho', 'entrada', 'salário']):
                        pending_type = BillType.INCOME
                        has_pending_transaction = True
                    # Verificar se menciona despesa
                    elif any(kw in msg_text for kw in ['despesa', 'gasto', 'pago', 'paguei']):
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
        
        if (expense_data and expense_data.get("action") == "create_expense") or (is_confirmation and has_pending_transaction and pending_amount):
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
                            due_date = datetime.fromisoformat(expense_data["due_date"]).date()
                        else:
                            due_date = date.today()
                    except:
                        due_date = date.today()
                
                # Determinar issuer baseado no tipo e histórico
                if expense_data and expense_data.get("issuer"):
                    default_issuer = expense_data.get("issuer")
                elif pending_issuer:
                    default_issuer = pending_issuer
                elif transaction_type == BillType.INCOME:
                    default_issuer = "Receita Manual"
                else:
                    default_issuer = "Despesa Manual"
                
                # Criar transação (não é boleto, é transação manual)
                # Usar o amount calculado (pode vir de expense_data ou pending_amount)
                final_amount = amount if amount else (expense_data.get("amount") if expense_data else 0)
                
                # Extrair categoria do expense_data ou usar padrão
                final_category = None
                if expense_data and expense_data.get("category"):
                    final_category = expense_data.get("category")
                elif transaction_type == BillType.INCOME:
                    final_category = "outras"  # Receitas geralmente não têm categoria específica
                
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
                
                if expense_data.get("is_installment"):
                    response_text += f" Esta é a parcela {expense_data.get('installment_current', 1)} de {expense_data.get('installment_total', 1)}."
                
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
📄 Fazer upload de boletos manualmente
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
📄 Fazer upload de boletos manualmente
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
📄 Fazer upload de boletos manualmente
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
📄 Fazer upload de boletos manualmente
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
📄 Fazer upload de boletos manualmente
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
📄 Fazer upload de boletos manualmente
📊 Visualizar seu dashboard
🔔 Configurar lembretes
💰 Adicionar despesas via formulário"""
            else:
                # Erros do Ollama
                if "timeout" in error_str:
                    response_text = """⏱️ O servidor de IA está demorando para responder.

Mas posso ajudá-lo com informações rápidas:

📄 **Upload de Boletos**: Acesse "Boletos" > "Upload"
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
📄 Fazer upload de boletos manualmente
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
• Orientar sobre upload de boletos
• Explicar como agendar pagamentos

**Para adicionar despesas via chat:**
Use comandos como:
• "Adicionar despesa de R$ 150,50 para energia elétrica"
• "Criar boleto de R$ 300,00 vencendo em 15/12/2024"

Por favor, verifique a configuração e tente novamente em alguns instantes."""
        
        return ChatResponse(response=response_text, action="chat")
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return ChatResponse(
            response="Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.",
            action="error"
        )

