import json
import logging
from typing import Dict, Optional, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

# Import condicional do Gemini
try:
    import google.generativeai as genai  # type: ignore
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None


class GeminiService:
    """Service for interacting with Google Gemini API for chat and extraction."""
    
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY não configurada. Configure no .env")
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.timeout = 10.0  # Gemini é muito rápido, 10s é suficiente
    
    async def chat(
        self, 
        message: str, 
        context: Dict = None, 
        conversation_history: List[Dict] = None
    ) -> str:
        """
        Chat with Gemini using user context and conversation history.
        """
        try:
            # Construir prompt com contexto
            system_prompt = self._build_system_prompt(context)
            user_prompt = self._build_user_prompt(message, conversation_history)
            
            # Preparar histórico da conversa para Gemini
            chat_history = []
            if conversation_history:
                for msg in conversation_history[-10:]:  # Últimas 10 mensagens
                    role = "user" if msg.get("sender") == "user" else "model"
                    chat_history.append({
                        "role": role,
                        "parts": [msg.get("text", "")]
                    })
            
            # Criar chat com histórico
            chat = self.model.start_chat(history=chat_history)
            
            # Enviar mensagem completa
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = chat.send_message(full_prompt)
            
            return response.text
            
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"Erro ao chamar Gemini: {e}", exc_info=True)
            
            # Mensagens de erro mais específicas
            if "api_key" in error_msg or "invalid api key" in error_msg or "authentication" in error_msg:
                raise ValueError("GEMINI_API_KEY inválida ou não configurada. Verifique a chave da API no Railway.")
            elif "quota" in error_msg or "limit" in error_msg or "rate limit" in error_msg:
                raise ValueError("Limite de requisições da API do Google excedido. Tente novamente mais tarde.")
            elif "timeout" in error_msg or "timed out" in error_msg:
                raise ValueError("Timeout ao conectar com a API do Google. Verifique sua conexão com a internet.")
            elif "connect" in error_msg or "connection" in error_msg or "network" in error_msg:
                raise ValueError("Erro de conexão com a API do Google. Verifique sua conexão com a internet.")
            elif "model" in error_msg or "not found" in error_msg:
                raise ValueError(f"Modelo {settings.GEMINI_MODEL} não encontrado. Verifique GEMINI_MODEL no Railway.")
            else:
                # Re-raise com mensagem genérica mas útil
                raise ValueError(f"Erro ao conectar com Gemini: {str(e)}")
    
    def _build_system_prompt(self, context: Dict = None) -> str:
        """Build system prompt with user financial context."""
        base_prompt = """Você é o assistente virtual do EconomizeIA. Seja direto, útil e objetivo.

## SEU ESTILO:
- Respostas curtas (1-2 frases máximo)
- Sem repetições - se o usuário confirmou, execute a ação imediatamente
- Seja objetivo: forneça informações ou execute ações
- Use emojis com moderação (apenas quando relevante)

## REGRAS CRÍTICAS:
1. NUNCA repita a mesma pergunta se o usuário já respondeu
2. Se o usuário confirmar algo ("sim", "pode", "confirma"), execute imediatamente
3. Se o usuário mencionar valor + tipo (receita/despesa), crie a transação sem perguntar mais
4. NUNCA diga "acesse o dashboard" - forneça a informação diretamente
5. Se não souber algo, seja honesto em 1 frase

## EXEMPLOS:
- Usuário: "adicionar R$ 2,00 de receita" → Resposta: "✅ Receita de R$ 2,00 adicionada!"
- Usuário: "sim" (após você perguntar) → Execute a ação, não pergunte novamente
- Usuário: "Quanto tenho pendente?" → Resposta: "R$ 0,00. Nenhum boleto pendente."

## IMPORTANTE:
- Seja direto e execute ações quando solicitado
- Não seja verboso ou repetitivo
- Foque em ajudar, não em conversar
"""
        
        if context:
            # Contexto otimizado - apenas dados essenciais
            context_text = f"Boletos: {context.get('total_bills', 0)} | Pendentes: {context.get('pending_bills', 0)} (R$ {context.get('total_pending', 0):.2f}) | Vencidos: {context.get('overdue_bills', 0)} | Mês: R$ {context.get('monthly_income', 0):.2f} receitas, R$ {context.get('monthly_expenses', 0):.2f} despesas, Saldo: R$ {context.get('monthly_balance', 0):.2f}"
            
            # Apenas alertas críticos
            if context.get('overdue_bills', 0) > 0:
                overdue = context.get('overdue_details', [])[:3]
                overdue_strs = []
                for b in overdue:
                    issuer = b.get('issuer', '?')
                    amount = b.get('amount', 0)
                    overdue_strs.append(f'{issuer} R${amount:.2f}')
                context_text += f" | ⚠️ Vencidos: {', '.join(overdue_strs)}"
            
            # Próximos 3 apenas
            if context.get('next_bills'):
                next_bills = context.get('next_bills', [])[:3]
                next_strs = []
                for b in next_bills:
                    issuer = b.get('issuer', '?')
                    amount = b.get('amount', 0)
                    days = b.get('days_until', 0)
                    next_strs.append(f'{issuer} R${amount:.2f} ({days}d)')
                context_text += f" | Próximos: {', '.join(next_strs)}"
            
            return base_prompt + "\n\nDados: " + context_text
        
        return base_prompt
    
    def _build_user_prompt(self, message: str, conversation_history: List[Dict] = None) -> str:
        """Build user prompt with message and optional history."""
        prompt = f"Usuário: {message}\n\nAssistente:"
        return prompt
    
    async def extract_expense_from_message(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Extract expense information from a natural language message using Gemini.
        Returns structured data if an expense creation command is detected, None otherwise.
        """
        system_prompt = """Você é um extrator especializado em informações de despesas e receitas a partir de mensagens em português brasileiro.

## OBJETIVO GERAL:
Interpretar mensagens em português e determinar, com precisão, se o usuário deseja registrar uma despesa ou receita. Quando a intenção for de criação, extrair todas as informações relevantes em formato estruturado. Quando não for comando, retornar apenas ação de chat.

## COMPORTAMENTO BASE:
Sempre analisar o texto natural do usuário, inferindo intenção, valores, datas, categorias, emissores, descrição e possíveis parcelamentos. Em caso de dúvida, optar por retornar {"action": "chat"} para evitar registros incorretos.

## DETECÇÃO DE INTENÇÃO:

A resposta deve começar identificando se a mensagem contém intenção explícita de criação de despesa ou receita, por meio de verbos ou comandos como:

**Para DESPESAS:**
adicionar, registrar, criar, lançar, inserir, anotar, colocar, pagar, comprei, gastei, paguei, despesa, gasto, saída, boleto, conta, pagamento

**Para RECEITAS:**
recebi, entrou, entrou dinheiro, ganho, faturamento, entrada, receita, adicionar receita, criar receita, registrar receita, ganhei, encontrei, achei

**Se a intenção não estiver clara, retornar:**
{"action": "chat"}

**Intenções típicas de chat** (perguntas, dúvidas, conversa geral, comandos não ligados a criação) devem sempre resultar em:
{"action": "chat"}

**A decisão nunca deve ser ambígua. Em caso de mínima incerteza sobre intenção de criação, retornar ação "chat".**

## EXTRAÇÃO DE INFORMAÇÕES:

Quando a intenção for criação, extrair:

### 2.1. VALOR MONETÁRIO:

O modelo deve identificar e converter valores escritos em múltiplos formatos:

**Aceitar os seguintes padrões:**
- Números com R$: "R$ 150,50", "R$150", "R$ 1.200"
- Números sem símbolo: "150,50", "150.50", "150", "1200"
- Textos por extenso: "cem reais", "cento e cinquenta reais", "mil e duzentos"
- Formatos com separadores variados: ponto, vírgula, espaço

**Regras obrigatórias:**
- Converter o valor final para decimal padrão: 150.50
- Se existir mais de um valor, escolher o mais provável conforme contexto (ex.: próximo de verbos como "paguei", "gastei", "custou")
- Se não houver valor claro, retornar "amount": null

### 2.2. DATAS:

O modelo deve reconhecer datas absolutas, relativas e textuais.

**Aceitar os seguintes formatos:**
- "15/12/2024"
- "15-12-2024"
- "15 de dezembro de 2024"
- "dia 20"
- Relativas: "amanhã", "ontem", "hoje", "próxima segunda", "semana que vem", "daqui a 3 dias"

**Regras obrigatórias:**
- Converter tudo para formato ISO: "YYYY-MM-DD"
- Se a data não puder ser inferida, "due_date": null
- Se houver mais de uma data, priorizar aquela relacionada ao pagamento ou lançamento, conforme verbos próximos

### 2.3. CATEGORIAS:

Usar palavras-chave do texto para classificar em UMA das categorias:

**Para DESPESAS:**
- **alimentacao**: comida, restaurante, supermercado, mercado, padaria, lanche, delivery, ifood
- **moradia**: aluguel, condomínio, água, luz, energia, gás, internet, telefone, IPTU
- **servicos**: serviço, manutenção, reparo, conserto, limpeza, técnico
- **transporte**: gasolina, combustível, uber, táxi, ônibus, metrô, estacionamento, pedágio, viagem
- **saude**: médico, remédio, farmácia, hospital, plano de saúde, dentista, consulta
- **vestuario**: roupas, vestuário, calçado, sapatos, tênis, camisa, calça, blusa, moda
- **compras**: compras, shopping, loja, adquirir, mercado, supermercado
- **lazer**: cinema, show, festa, diversão, jogos, entretenimento
- **educacao**: escola, curso, faculdade, universidade, livro, material escolar
- **outras**: qualquer despesa não mapeada nas categorias acima

**Para RECEITAS:**
- **investimentos**: salário, salario, freelance, freela, vendas, comissão, comissao, bonus, bônus, renda, dividendos, juros, aplicação, aplicacao, poupança, poupanca, ações, acoes, investimento, reembolso, aluguel recebido, emprestimo, empréstimo
- **outras**: qualquer receita não mapeada (use apenas se realmente não se encaixar em investimentos)

**Regras obrigatórias:**
- Para RECEITAS: sempre usar "investimentos" quando for salário, freelance, vendas, comissões, bônus, dividendos, juros, aplicações, etc.
- Para DESPESAS: nunca classificar como "outras" quando existir categoria mais específica
- Receitas de salário, freelance, vendas, comissões devem SEMPRE ser categorizadas como "investimentos"

### 2.4. EMISSOR / FORNECEDOR:

Extrair o nome da empresa, loja, serviço ou pessoa envolvida.

**Exemplos:**
- Supermercado X
- Loja Y
- Energia Elétrica
- Uber
- iFood
- Dentista João Silva

**Regra:**
- Se não houver emissor claro, usar "issuer": null

### 2.5. PARCELAMENTO:

Detectar padrões como:
- "parcelado"
- "parcela"
- "em X vezes"
- "dividido em"
- "financiado"
- "2 de 10"

**Quando detectado:**
- "is_installment": true
- Extrair "installment_total" e "installment_current" quando possível

**Exemplos:**
- "em 10 vezes": current = null, total = 10
- "2 de 10": current = 2, total = 10

**Se não houver parcelamento:**
- "is_installment": false
- "installment_total": null
- "installment_current": null

### 2.6. DESCRIÇÃO:

Se o texto contiver detalhamento adicional não classificado, usá-lo como descrição.
Se não houver, usar "description": null

## FORMATO DE RESPOSTA:

Sempre retornar JSON puro, sem markdown, sem texto extra, sem comentários:

**Quando for comando de criação COMPLETO (tem valor e categoria/emissor):**
{
  "action": "create_expense" ou "create_income",
  "amount": 150.50,
  "issuer": "Nome da empresa ou null",
  "due_date": "2024-12-15 ou null",
  "category": "alimentacao|moradia|servicos|transporte|saude|vestuario|compras|lazer|educacao|investimentos|outras",
  "description": "texto ou null",
  "is_installment": false,
  "installment_total": null,
  "installment_current": null,
  "needs_info": false,
  "missing_info": null
}

**Quando for comando de criação mas FALTAR informação importante (valor OK mas sem categoria/emissor):**
{
  "action": "ask_for_info",
  "amount": 300.00,
  "issuer": null,
  "due_date": null,
  "category": null,
  "description": null,
  "is_installment": false,
  "installment_total": null,
  "installment_current": null,
  "needs_info": true,
  "missing_info": "category" ou "issuer" ou "category_and_issuer"
}

**Quando não for comando:**
{
  "action": "chat"
}

## REGRAS CRÍTICAS:

1. Responder exclusivamente em JSON válido
2. Não adicionar explicações externas ao JSON
3. Em dúvida, sempre retornar "action": "chat"
4. Ser rigoroso na conversão de valores e datas
5. Nunca inferir categoria errada
6. Sempre evitar ambiguidade

## DETECÇÃO DE INFORMAÇÕES FALTANTES:

**Quando detectar intenção de criação mas faltar informação importante:**

- Se tiver VALOR mas NÃO tiver CATEGORIA nem EMISSOR: retornar "action": "ask_for_info", "missing_info": "category_and_issuer"
- Se tiver VALOR e CATEGORIA mas NÃO tiver EMISSOR: retornar "action": "ask_for_info", "missing_info": "issuer"
- Se tiver VALOR e EMISSOR mas NÃO tiver CATEGORIA: retornar "action": "ask_for_info", "missing_info": "category"
- Se tiver VALOR, CATEGORIA e EMISSOR: retornar "action": "create_expense" ou "create_income"

**Exemplos de quando perguntar:**

- "Gastei 300 reais" → falta categoria e emissor → "ask_for_info"
- "Paguei 150 reais" → falta categoria e emissor → "ask_for_info"
- "Recebi 500 reais" → falta emissor (receitas não precisam de categoria) → pode criar direto ou perguntar emissor

## EXEMPLOS APRIMORADOS:

**Entrada:** "Adicionar despesa de R$ 150,50 para energia elétrica"
**Saída:**
{
  "action": "create_expense",
  "amount": 150.50,
  "issuer": "Energia Elétrica",
  "due_date": null,
  "category": "moradia",
  "description": null,
  "is_installment": false,
  "installment_total": null,
  "installment_current": null
}

**Entrada:** "Gastei com compras R$ 200"
**Saída:**
{
  "action": "create_expense",
  "amount": 200.00,
  "issuer": null,
  "due_date": null,
  "category": "compras",
  "description": null,
  "is_installment": false,
  "installment_total": null,
  "installment_current": null
}

**Entrada:** "Quero ver meus boletos"
**Saída:**
{
  "action": "chat"
}"""
        
        try:
            response = self.model.generate_content(
                f"{system_prompt}\n\nMensagem do usuário: {message}\n\nJSON:"
            )
            
            # Extrair JSON da resposta
            response_text = response.text.strip()
            
            # Tentar extrair JSON se houver markdown
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            try:
                extracted_data = json.loads(response_text)
                return extracted_data
            except json.JSONDecodeError:
                logger.error(f"Gemini retornou JSON inválido: {response_text}")
                return {"action": "chat"}
                
        except Exception as e:
            logger.error(f"Erro ao extrair despesa com Gemini: {e}", exc_info=True)
            return {"action": "chat"}
    
    async def extract_bill_fields(self, ocr_text: str, image_url: Optional[str] = None, 
                                  metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract structured fields from OCR text using Gemini.
        Returns extracted fields with confidence score.
        """
        system_prompt = """Você é um extrator de campos de documentos financeiros. Receberá linhas de OCR e opcionalmente a URL da imagem. Deve retornar apenas JSON estrito conforme o schema.

Task: Extraia e normalize os campos:
{
  "issuer": "string or null",
  "amount": "decimal or null",
  "currency": "BRL",
  "due_date": "YYYY-MM-DD or null",
  "barcode": "string or null",
  "payment_place": "string or null",
  "confidence": 0.0-1.0,
  "notes": "string"
}

Rules:
1. Datas em ISO (YYYY-MM-DD).
2. Valores numéricos com duas casas decimais.
3. Se algum campo foi inferido, reduzir confidence < 0.9 e documentar em notes.
4. Corrija erros óbvios do OCR (ex: R0$ -> R$, 0 -> O quando apropriado).
5. Responder somente JSON válido, sem markdown, sem texto adicional."""
        
        user_prompt = f"""Extraia os campos do documento financeiro abaixo:

OCR Text:
{ocr_text[:2000]}

Metadata: {json.dumps(metadata or {})}"""
        
        try:
            response = self.model.generate_content(
                f"{system_prompt}\n\n{user_prompt}"
            )
            
            response_text = response.text.strip()
            
            # Try to parse JSON (might be wrapped in markdown)
            try:
                # Remove markdown code blocks if present
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                extracted = json.loads(response_text)
                
                # Validate and normalize
                if "currency" not in extracted:
                    extracted["currency"] = "BRL"
                
                # Calcular confiança baseada nos campos extraídos se não foi fornecida ou for 0.0
                if "confidence" not in extracted or extracted.get("confidence", 0.0) == 0.0:
                    extracted["confidence"] = self._calculate_confidence(extracted)
                
                return extracted
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini JSON response: {e}")
                logger.error(f"Response was: {response_text[:500]}")
                return {
                    "issuer": None,
                    "amount": None,
                    "currency": "BRL",
                    "due_date": None,
                    "barcode": None,
                    "payment_place": None,
                    "confidence": 0.3,
                    "notes": f"Erro ao processar resposta: {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"Erro ao extrair campos com Gemini: {e}", exc_info=True)
            error_result = {
                "issuer": None,
                "amount": None,
                "currency": "BRL",
                "due_date": None,
                "barcode": None,
                "payment_place": None,
                "confidence": 0.3,  # Mínimo 30% mesmo em erro
                "notes": f"Erro ao processar: {str(e)}"
            }
            error_result["confidence"] = self._calculate_confidence(error_result)
            return error_result
    
    def _calculate_confidence(self, extracted: Dict[str, Any]) -> float:
        """
        Calcula confiança baseada nos campos extraídos.
        - amount + due_date: 0.85-0.9
        - amount OU due_date: 0.6-0.7
        - issuer apenas: 0.4-0.5
        - Nada: 0.3
        """
        has_amount = extracted.get("amount") is not None and extracted.get("amount") != 0
        has_due_date = extracted.get("due_date") is not None
        has_issuer = extracted.get("issuer") is not None and extracted.get("issuer") != ""
        has_barcode = extracted.get("barcode") is not None and extracted.get("barcode") != ""
        
        if has_amount and has_due_date:
            # Campos principais extraídos: alta confiança
            base_confidence = 0.85
            if has_issuer:
                base_confidence += 0.05
            if has_barcode:
                base_confidence += 0.05
            return min(base_confidence, 0.95)
        elif has_amount or has_due_date:
            # Apenas um campo principal: média confiança
            return 0.65 if has_issuer else 0.55
        elif has_issuer:
            # Apenas emissor: baixa confiança
            return 0.45
        else:
            # Nada extraído: muito baixa confiança
            return 0.3


# Instância global do serviço
gemini_service: Optional[GeminiService] = None

def get_gemini_service() -> Optional[GeminiService]:
    """Get or create Gemini service instance."""
    global gemini_service
    if not GEMINI_AVAILABLE:
        return None
    
    if settings.USE_GEMINI and settings.GEMINI_API_KEY:
        if gemini_service is None:
            try:
                gemini_service = GeminiService()
            except Exception as e:
                logger.error(f"Erro ao inicializar Gemini: {e}")
                return None
        return gemini_service
    return None

