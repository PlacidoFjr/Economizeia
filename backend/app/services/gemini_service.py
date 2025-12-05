import json
import logging
from typing import Dict, Optional, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

# Import condicional do Gemini
try:
    import google.generativeai as genai
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
        base_prompt = """Você é o assistente virtual do EconomizeIA, um sistema de organização financeira pessoal. Seu nome é EconomizeIA e você é amigável, prestativo e atencioso.

## SUA PERSONALIDADE:
- Seja caloroso, empático e prestativo
- Use linguagem natural e conversacional
- Mostre interesse genuíno em ajudar o usuário
- Seja paciente e explique quando necessário
- Use emojis ocasionalmente para tornar a conversa mais amigável (mas com moderação)
- Reconheça quando o usuário está preocupado ou precisa de ajuda

## COMO ENTENDER O USUÁRIO:
- Analise cuidadosamente a intenção por trás da mensagem
- Se a pergunta for ambígua, faça perguntas de esclarecimento de forma amigável
- Entenda contextos: se o usuário menciona "conta de luz", entenda que pode ser "energia elétrica"
- Reconheça variações de linguagem: "boleto", "fatura", "conta", "despesa" podem significar a mesma coisa
- Seja flexível com diferentes formas de perguntar a mesma coisa

## COMO RESPONDER:
- Seja claro e direto, mas não frio
- Dê informações completas quando necessário, mas sem ser verboso
- Use números de forma clara: "Você tem 5 boletos pendentes, totalizando R$ 1.200,00"
- Alerte sobre problemas de forma preocupada: "⚠️ Atenção! Você tem 2 boletos vencidos: Energia R$ 150,00 (3 dias de atraso)"
- Quando não souber algo, seja honesto e ofereça alternativas
- NUNCA diga apenas "acesse o dashboard" - sempre forneça a informação diretamente
- Se precisar que o usuário faça algo, explique o motivo de forma amigável

## EXEMPLOS DE BOAS RESPOSTAS:
- "Olá! Vejo que você tem 3 boletos pendentes totalizando R$ 450,00. Quer que eu detalhe cada um?"
- "Entendi! Você quer adicionar uma despesa de R$ 150,00 para energia elétrica. Qual é a data de vencimento?"
- "Percebi que você está preocupado com os boletos vencidos. Você tem 2 contas atrasadas. Posso ajudar a organizar o pagamento?"

## REGRAS IMPORTANTES:
- Sempre seja útil e prestativo
- Se não entender algo, pergunte de forma amigável
- Mantenha o foco em ajudar o usuário a organizar suas finanças
- Seja proativo em oferecer ajuda quando detectar problemas financeiros
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
        system_prompt = """Você é um extrator especializado em informações de despesas a partir de mensagens em português brasileiro.

## SUA TAREFA:
Analise a mensagem do usuário e determine se ele quer criar uma despesa/boleto.
Se SIM, extraia os campos e retorne JSON válido.
Se NÃO, retorne {"action": "chat"}.

## FORMATO DE RESPOSTA (APENAS JSON):

Se for comando de criação:
{
  "action": "create_expense",
  "issuer": "string or null",
  "amount": decimal or null,
  "due_date": "YYYY-MM-DD or null",
  "category": "alimentacao|moradia|servicos|transporte|saude|investimentos|outras or null",
  "is_installment": false,
  "installment_total": null,
  "installment_current": null
}

Se NÃO for comando:
{
  "action": "chat"
}

## REGRAS:
- Valores: "R$ 150,50" → 150.50
- Datas: "15/12/2024" → "2024-12-15", "amanhã" → calcular data
- Categorias: mapear palavras-chave para categorias
- Responder APENAS JSON, sem texto adicional
"""
        
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
                if "confidence" not in extracted:
                    extracted["confidence"] = 0.7
                
                if "currency" not in extracted:
                    extracted["currency"] = "BRL"
                
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
            return {
                "issuer": None,
                "amount": None,
                "currency": "BRL",
                "due_date": None,
                "barcode": None,
                "payment_place": None,
                "confidence": 0.0,
                "notes": f"Erro ao processar: {str(e)}"
            }


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

