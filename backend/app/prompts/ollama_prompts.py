"""
Templates de prompt para Ollama
"""

EXTRACTION_SYSTEM_PROMPT = """Você é um extrator de campos de documentos financeiros. Receberá linhas de OCR e opcionalmente a URL da imagem. Deve retornar apenas JSON estrito conforme o schema.

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


CATEGORIZATION_SYSTEM_PROMPT = """Você é um classificador financeiro que conhece histórico do usuário.

Task: Retorne JSON:
{
  "category": "alimentacao|moradia|servicos|transporte|saude|investimentos|outras",
  "category_confidence": 0-1,
  "anomaly": true|false,
  "anomaly_score": 0-1,
  "suggested_actions": ["verificar_transacao","revisar_assinatura","bloquear_cartao"]
}

Rules: usar histórico do usuário para detectar anomalias. Responder apenas JSON válido."""


def build_extraction_prompt(ocr_text: str, image_url: str = None, metadata: dict = None) -> str:
    """Build extraction prompt for Ollama."""
    user_input = {
        "ocr_lines": ocr_text.split('\n') if ocr_text else [],
        "image_url": image_url,
        "meta": metadata or {}
    }
    
    prompt = f"""Extraia os campos do documento financeiro abaixo:

OCR Text:
{ocr_text[:2000]}  # Limit to avoid token limits

Metadata: {user_input['meta']}"""
    
    return prompt


def build_categorization_prompt(description: str, amount: float, user_profile: dict = None) -> str:
    """Build categorization prompt for Ollama."""
    import json
    prompt = f"""Classifique a transação e detecte anomalias:

Descrição: {description}
Valor: R$ {amount:.2f}
Perfil do usuário: {json.dumps(user_profile or {})}"""
    
    return prompt

