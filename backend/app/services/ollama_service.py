import httpx
import json
import logging
from typing import Dict, Optional, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """Service for interacting with Ollama API for semantic extraction and classification."""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = 25.0  # Timeout de 25s - balanceado entre rapidez e completude
        # Modelos vision-capable do Ollama que podem fazer OCR direto
        self.vision_models = ["llava", "bakllava", "llava:13b", "llava:7b"]
        self.supports_vision = any(vm in self.model.lower() for vm in self.vision_models)
    
    async def extract_bill_fields(self, ocr_text: str, image_url: Optional[str] = None, 
                                  metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract structured fields from OCR text using Ollama.
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

        user_input = {
            "ocr_lines": ocr_text.split('\n') if ocr_text else [],
            "image_url": image_url,
            "meta": metadata or {}
        }
        
        user_prompt = f"""Extraia os campos do documento financeiro abaixo:

OCR Text:
{ocr_text[:2000]}  # Limit to avoid token limits

Metadata: {json.dumps(user_input['meta'])}"""

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "system": system_prompt,
                        "prompt": user_prompt,
                        "format": "json",
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                # Extract JSON from response
                response_text = result.get("response", "")
                
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
                    logger.error(f"Failed to parse Ollama JSON response: {e}")
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
                    
        except httpx.TimeoutException:
            logger.error("Ollama request timeout")
            return {
                "issuer": None,
                "amount": None,
                "currency": "BRL",
                "due_date": None,
                "barcode": None,
                "payment_place": None,
                "confidence": 0.0,
                "notes": "Timeout ao processar com Ollama"
            }
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return {
                "issuer": None,
                "amount": None,
                "currency": "BRL",
                "due_date": None,
                "barcode": None,
                "payment_place": None,
                "confidence": 0.3,  # Mínimo 30% mesmo em erro
                "notes": f"Erro: {str(e)}"
            }
    
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
    
    async def categorize_and_detect_anomaly(self, description: str, amount: float,
                                           user_profile: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Categorize transaction and detect anomalies using Ollama.
        """
        system_prompt = """Você é um classificador financeiro que conhece histórico do usuário.

Task: Retorne JSON:
{
  "category": "alimentacao|moradia|servicos|transporte|saude|investimentos|outras",
  "category_confidence": 0-1,
  "anomaly": true|false,
  "anomaly_score": 0-1,
  "suggested_actions": ["verificar_transacao","revisar_assinatura","bloquear_cartao"]
}

Rules: usar histórico do usuário para detectar anomalias. Responder apenas JSON válido."""

        user_prompt = f"""Classifique a transação e detecte anomalias:

Descrição: {description}
Valor: R$ {amount:.2f}
Perfil do usuário: {json.dumps(user_profile or {})}"""

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "system": system_prompt,
                        "prompt": user_prompt,
                        "format": "json",
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                response_text = result.get("response", "")
                
                # Parse JSON
                try:
                    if "```json" in response_text:
                        response_text = response_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in response_text:
                        response_text = response_text.split("```")[1].split("```")[0].strip()
                    
                    return json.loads(response_text)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse categorization JSON: {e}")
                    return {
                        "category": "outras",
                        "category_confidence": 0.5,
                        "anomaly": False,
                        "anomaly_score": 0.0,
                        "suggested_actions": []
                    }
                    
        except Exception as e:
            logger.error(f"Error in categorization: {e}")
            return {
                "category": "outras",
                "category_confidence": 0.5,
                "anomaly": False,
                "anomaly_score": 0.0,
                "suggested_actions": []
            }
    
    async def extract_expense_from_message(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Extract expense information from a natural language message.
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
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "system": system_prompt,
                        "prompt": f"Extraia informações da mensagem: {message}",
                        "format": "json",
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                response_text = result.get("response", "")
                
                # Parse JSON
                try:
                    if "```json" in response_text:
                        response_text = response_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in response_text:
                        response_text = response_text.split("```")[1].split("```")[0].strip()
                    
                    extracted = json.loads(response_text)
                    
                    # Se não for ação de criar despesa, retornar None
                    if extracted.get("action") != "create_expense":
                        return None
                    
                    return extracted
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse expense extraction JSON: {e}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error extracting expense from message: {e}")
            return None
    
    async def chat(self, message: str, context: Optional[Dict] = None, 
                   conversation_history: Optional[list] = None) -> str:
        """
        Chat with Ollama for conversational assistance.
        Returns a natural language response.
        """
        # Respostas rápidas para perguntas comuns (cache - sem chamar Ollama)
        message_lower = message.lower().strip()
        quick_responses = {
            # Saudações
            "ola": "Olá! Como posso ajudá-lo hoje?",
            "oi": "Oi! Em que posso ajudar?",
            "olá": "Olá! Como posso ajudá-lo hoje?",
            "bom dia": "Bom dia! Como posso ajudá-lo?",
            "boa tarde": "Boa tarde! Como posso ajudá-lo?",
            "boa noite": "Boa noite! Como posso ajudá-lo?",
            
            # Funcionalidades
            "o que você consegue fazer": """Posso ajudá-lo com:

📄 **Upload de Boletos** - Envie seus boletos e faturas para extração automática
📊 **Dashboard** - Visualize seus gastos e receitas em gráficos
🔔 **Lembretes** - Receba notificações antes dos vencimentos
🤖 **Assistente** - Adicione despesas via chat com comandos naturais
📋 **Relatórios** - Acompanhe sua situação financeira

**Para adicionar despesas via chat:**
"Adicionar despesa de R$ 150,50 para energia elétrica"
"Criar boleto de R$ 300,00 vencendo em 15/12/2024"

Como posso ajudá-lo hoje?""",
            
            "o que vc consegue fazer": """Posso ajudá-lo com:

📄 **Upload de Boletos** - Envie seus boletos e faturas para extração automática
📊 **Dashboard** - Visualize seus gastos e receitas em gráficos
🔔 **Lembretes** - Receba notificações antes dos vencimentos
🤖 **Assistente** - Adicione despesas via chat com comandos naturais
📋 **Relatórios** - Acompanhe sua situação financeira

**Para adicionar despesas via chat:**
"Adicionar despesa de R$ 150,50 para energia elétrica"
"Criar boleto de R$ 300,00 vencendo em 15/12/2024"

Como posso ajudá-lo hoje?""",
            
            "como adicionar despesa": """Você pode adicionar despesas de duas formas:

1️⃣ **Via Chat** (mais rápido):
   - "Adicionar despesa de R$ 150,50 para energia elétrica"
   - "Criar boleto de R$ 300,00 vencendo em 15/12/2024"
   - "Adicionar gasto de R$ 50,00 com alimentação"

2️⃣ **Via Upload**:
   - Acesse "Boletos" > "Upload"
   - Envie o PDF/foto do boleto
   - O sistema extrai as informações automaticamente

Qual método você prefere usar?""",
            
            "como fazer upload": """Para fazer upload de boletos:

1. Acesse o menu "Boletos"
2. Clique em "Upload" ou "Adicionar Boleto"
3. Arraste o arquivo PDF ou foto do boleto
4. O sistema extrai automaticamente:
   - Valor
   - Data de vencimento
   - Emissor
   - Código de barras
5. Revise e confirme os dados

Dica: Funciona com PDFs e imagens (JPG, PNG)""",
            
            # Removidas respostas genéricas - agora o chatbot usa dados reais
        }
        
        # Verificar se há resposta rápida (cache) - busca mais flexível
        for key, response in quick_responses.items():
            if key in message_lower or message_lower.startswith(key) or message_lower.endswith(key):
                return response
        
        # Construir prompt inteligente com TODOS os dados do usuário
        system_prompt = """Você é o assistente financeiro inteligente do EconomizeIA. Você tem ACESSO COMPLETO aos dados financeiros do usuário.

REGRAS IMPORTANTES:
1. SEMPRE use os DADOS REAIS do usuário nas respostas - não dê instruções genéricas
2. Seja PROATIVO - analise os dados e ofereça insights
3. Responda com NÚMEROS e FATOS reais do usuário
4. Se o usuário perguntar "quantos boletos", responda o número EXATO
5. Se perguntar "quanto tenho pendente", responda o valor EXATO em R$
6. Se perguntar sobre categorias, liste as categorias REAIS do usuário
7. Se houver boletos vencidos, ALERTE o usuário com detalhes
8. Aprenda o padrão de gastos do usuário e ofereça sugestões personalizadas
9. Seja CONVERSACIONAL e ÚTIL, não apenas um guia
10. Use os dados para dar conselhos financeiros personalizados

NUNCA diga "acesse o dashboard" - você TEM os dados, USE-OS na resposta!

Responda em português brasileiro de forma natural e conversacional."""

        # Construir contexto OTIMIZADO do usuário (reduzido para evitar timeout)
        context_text = ""
        if context:
            # Resumo compacto - apenas dados essenciais
            context_text = f"""DADOS DO USUÁRIO:
- Boletos: {context.get('total_bills', 0)} total, {context.get('pending_bills', 0)} pendentes (R$ {context.get('total_pending', 0):.2f}), {context.get('overdue_bills', 0)} vencidos
- Mês atual: Receitas R$ {context.get('monthly_income', 0):.2f}, Despesas R$ {context.get('monthly_expenses', 0):.2f}, Saldo R$ {context.get('monthly_balance', 0):.2f}

"""
            
            # Boletos vencidos (máximo 3)
            if context.get('overdue_bills', 0) > 0:
                context_text += f"Vencidos: "
                overdue_list = []
                for bill in context.get('overdue_details', [])[:3]:
                    overdue_list.append(f"{bill.get('issuer', '?')} R${bill.get('amount', 0):.2f} ({bill.get('days_overdue', 0)}d)")
                context_text += ", ".join(overdue_list) + "\n"
            
            # Próximos boletos (máximo 3)
            if context.get('next_bills'):
                context_text += "Próximos: "
                next_list = []
                for bill in context.get('next_bills', [])[:3]:
                    next_list.append(f"{bill.get('issuer', '?')} R${bill.get('amount', 0):.2f} ({bill.get('days_until', 0)}d)")
                context_text += ", ".join(next_list) + "\n"
            
            # Top 3 categorias apenas
            if context.get('categories'):
                sorted_cats = sorted(context.get('categories', {}).items(), key=lambda x: x[1].get('total', 0), reverse=True)
                top_cats = []
                for cat, data in sorted_cats[:3]:
                    top_cats.append(f"{cat} R${data.get('total', 0):.2f}")
                context_text += f"Categorias: {', '.join(top_cats)}\n"
            
            # Top 3 emissores apenas
            if context.get('top_issuers'):
                top_issuers_list = []
                for issuer, data in list(context.get('top_issuers', {}).items())[:3]:
                    top_issuers_list.append(f"{issuer} R${data.get('total', 0):.2f}")
                context_text += f"Emissores: {', '.join(top_issuers_list)}\n"

        # Histórico da conversa (últimas 3 mensagens - reduzido para otimizar)
        history_text = ""
        if conversation_history and len(conversation_history) > 0:
            recent_history = conversation_history[-3:]  # Reduzido para 3 mensagens
            for msg in recent_history:
                role = "U" if msg.get("sender") == "user" else "A"
                history_text += f"{role}: {msg.get('text', '')}\n"

        user_prompt = f"""{context_text}
Histórico: {history_text}
U: {message}
A:"""

        try:
            # Log para debug (apenas em desenvolvimento)
            logger.info(f"Enviando requisição ao Ollama - Modelo: {self.model}, Contexto: ~{len(user_prompt)} chars")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "system": system_prompt,
                        "prompt": user_prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "num_predict": 150,  # Reduzido ainda mais para respostas mais rápidas
                            "num_ctx": 1536,  # Reduzido para 1536 (mais rápido que 2048)
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                response_text = result.get("response", "").strip()
                
                # Log de sucesso
                logger.info(f"Resposta do Ollama recebida: {len(response_text)} caracteres")
                
                # Limpar resposta se necessário
                if not response_text:
                    return "Desculpe, não consegui processar sua pergunta. Pode reformular?"
                
                return response_text
                
        except httpx.TimeoutException:
            logger.error("Ollama chat timeout")
            # Se temos contexto, usar dados reais mesmo com timeout
            if context:
                context_summary = f"""⏱️ O servidor de IA está demorando, mas posso te dar informações rápidas dos seus dados:

📊 **Resumo:**
- Total de boletos: {context.get('total_bills', 0)}
- Pendentes: {context.get('pending_bills', 0)} (R$ {context.get('total_pending', 0):.2f})
- Vencidos: {context.get('overdue_bills', 0)}
- Saldo do mês: R$ {context.get('monthly_balance', 0):.2f}

"""
                if context.get('overdue_bills', 0) > 0:
                    context_summary += f"⚠️ Você tem {context.get('overdue_bills', 0)} boletos vencidos!\n\n"
                if context.get('next_bills'):
                    context_summary += "📅 Próximos vencimentos:\n"
                    for bill in context.get('next_bills', [])[:3]:
                        context_summary += f"- {bill.get('issuer', 'Desconhecido')}: R$ {bill.get('amount', 0):.2f} (em {bill.get('days_until', 0)} dias)\n"
                return context_summary + "\nTente novamente em alguns instantes para uma análise mais completa."
            else:
                return """⏱️ O servidor de IA está demorando para responder.

Mas posso ajudá-lo com informações rápidas:

📄 **Upload de Boletos**: Acesse "Boletos" > "Upload"
📊 **Dashboard**: Veja seus gastos e receitas
🔔 **Lembretes**: Configure notificações antes dos vencimentos
🤖 **Adicionar Despesa**: Digite "Adicionar despesa de R$ 150,50 para energia"

Tente novamente em alguns instantes ou use as funcionalidades do menu."""
        except httpx.ConnectError:
            logger.error("Ollama connection error - service not available")
            return """⚠️ O servidor de IA (Ollama) não está disponível no momento.

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
        except Exception as e:
            logger.error(f"Error in Ollama chat: {e}")
            return f"Desculpe, ocorreu um erro ao processar sua mensagem: {str(e)[:100]}. Por favor, tente novamente."


ollama_service = OllamaService()

