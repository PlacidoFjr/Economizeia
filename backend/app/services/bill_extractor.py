"""
Extrator específico para boletos bancários brasileiros.
Extrai APENAS campos essenciais: valor, vencimento, beneficiário e código de barras.
"""
import re
import logging
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class BrazilianBillExtractor:
    """Extrator especializado para boletos brasileiros - apenas campos essenciais."""
    
    def __init__(self):
        # Padrões regex apenas para campos ESSENCIAIS
        self.patterns = {
            # Código de barras (44 dígitos) - essencial para pagamento
            'codigo_barras': re.compile(r'(\d{44})'),
            
            # Linha digitável (pode converter para código de barras)
            'linha_digitavel': re.compile(
                r'(\d{5}\.\d{5}\s+\d{5}\.\d{6}\s+\d{5}\.\d{6}\s+\d\s+\d{14})',
                re.IGNORECASE
            ),
            
            # Valor do documento - ESSENCIAL
            'valor': re.compile(
                r'(?:valor\s+(?:do\s+)?documento|(=)\s*valor)[:\s]*R?\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d+,\d{2})',
                re.IGNORECASE
            ),
            
            # Data de vencimento - ESSENCIAL
            'vencimento': re.compile(
                r'(?:vencimento|venc\.)[:\s]*(\d{2}/\d{2}/\d{4})',
                re.IGNORECASE
            ),
            
            # Beneficiário/Emissor - útil para identificar
            'beneficiario': re.compile(
                r'benefici[áa]rio[:\s]*([A-Z][A-Z\s\-]+?)(?:\s+CNPJ|CPF|$|\n|\d)',
                re.IGNORECASE
            ),
        }
    
    def extract_fields(self, ocr_text: str) -> Dict[str, Any]:
        """
        Extrai APENAS campos essenciais de boletos brasileiros.
        Campos: valor, vencimento, beneficiário, código de barras.
        """
        if not ocr_text or len(ocr_text.strip()) < 10:
            logger.warning("Texto OCR vazio ou muito curto")
            return self._empty_result("Texto OCR vazio ou muito curto")
        
        # Log do texto OCR para debug (primeiros 500 caracteres)
        logger.info(f"Texto OCR recebido ({len(ocr_text)} caracteres): {ocr_text[:500]}...")
        
        # Normalizar texto (manter quebras de linha para melhor matching)
        normalized_text = re.sub(r'\s+', ' ', ocr_text)
        normalized_text_with_newlines = ocr_text  # Manter original com quebras
        
        extracted = {
            "issuer": None,
            "amount": None,
            "currency": "BRL",
            "due_date": None,
            "barcode": None,
            "payment_place": None,
            "confidence": 0.0,
            "notes": ""
        }
        
        # 1. Extrair código de barras (prioridade - essencial para pagamento)
        barcode_match = self.patterns['codigo_barras'].search(normalized_text)
        if barcode_match:
            extracted["barcode"] = barcode_match.group(1)
            logger.info(f"✅ Código de barras encontrado: {extracted['barcode'][:10]}...")
        else:
            # Tentar linha digitável e converter
            linha_match = self.patterns['linha_digitavel'].search(normalized_text)
            if linha_match:
                linha_digitavel = linha_match.group(1).replace(' ', '').replace('.', '')
                if len(linha_digitavel) >= 44:
                    extracted["barcode"] = linha_digitavel[:44]
                    logger.info(f"✅ Código de barras extraído da linha digitável: {extracted['barcode'][:10]}...")
            else:
                logger.warning("❌ Código de barras não encontrado")
        
        # 2. Extrair VALOR (essencial) - padrões mais flexíveis
        # Tentar múltiplos padrões
        valor_patterns = [
            r'(?:valor\s+(?:do\s+)?documento|(=)\s*valor)[:\s]*R?\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d+,\d{2})',
            r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d+,\d{2})',
            r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*(?:reais|R\$)',
            r'valor[:\s]*(\d+,\d{2})',
        ]
        
        valor_str = None
        for pattern in valor_patterns:
            valor_match = re.search(pattern, normalized_text, re.IGNORECASE)
            if valor_match:
                # Pegar o grupo que contém o valor (último grupo numérico)
                groups = valor_match.groups()
                for group in reversed(groups):
                    if group and re.match(r'\d', group):
                        valor_str = group
                        break
                if valor_str:
                    break
        
        if valor_str:
            try:
                # Converter formato brasileiro (1.234,56 ou 0,02) para float
                valor_clean = valor_str.replace('.', '').replace(',', '.')
                extracted["amount"] = float(valor_clean)
                logger.info(f"✅ Valor extraído: R$ {extracted['amount']:.2f}")
            except (ValueError, AttributeError) as e:
                logger.warning(f"❌ Erro ao converter valor '{valor_str}': {e}")
        else:
            logger.warning("❌ Valor não encontrado no texto OCR")
        
        # 3. Extrair DATA DE VENCIMENTO (essencial) - padrões mais flexíveis
        date_patterns = [
            r'(?:vencimento|venc\.)[:\s]*(\d{2}/\d{2}/\d{4})',
            r'(\d{2}/\d{2}/\d{4})',  # Qualquer data no formato DD/MM/AAAA
        ]
        
        data_str = None
        for pattern in date_patterns:
            vencimento_match = re.search(pattern, normalized_text, re.IGNORECASE)
            if vencimento_match:
                data_str = vencimento_match.group(1)
                # Validar se é uma data válida
                try:
                    datetime.strptime(data_str, '%d/%m/%Y')
                    break
                except ValueError:
                    continue
        
        if data_str:
            try:
                # Converter DD/MM/AAAA para YYYY-MM-DD
                data_obj = datetime.strptime(data_str, '%d/%m/%Y')
                extracted["due_date"] = data_obj.strftime('%Y-%m-%d')
                logger.info(f"✅ Data de vencimento extraída: {extracted['due_date']}")
            except ValueError as e:
                logger.warning(f"❌ Erro ao converter data '{data_str}': {e}")
        else:
            logger.warning("❌ Data de vencimento não encontrada")
        
        # 4. Extrair BENEFICIÁRIO/EMISSOR (útil para identificar) - padrões mais flexíveis
        beneficiario_patterns = [
            r'benefici[áa]rio[:\s]*([A-Z][A-Z\s\-]+?)(?:\s+CNPJ|CPF|$|\n|\d)',
            r'([A-Z][A-Z\s\-]{2,50}?)\s*-\s*CNPJ',
            r'([A-Z][A-Z\s]+?)\s+CNPJ',
        ]
        
        for pattern in beneficiario_patterns:
            beneficiario_match = re.search(pattern, normalized_text_with_newlines, re.IGNORECASE | re.MULTILINE)
            if beneficiario_match:
                beneficiario = beneficiario_match.group(1).strip()
                # Limpar: remover CNPJ/CPF e caracteres especiais
                beneficiario = re.sub(r'\s+CNPJ.*$', '', beneficiario, flags=re.IGNORECASE)
                beneficiario = re.sub(r'\s+CPF.*$', '', beneficiario, flags=re.IGNORECASE)
                beneficiario = beneficiario.strip()
                # Limitar tamanho (nomes muito longos podem ser erros de OCR)
                if 3 <= len(beneficiario) <= 100:
                    extracted["issuer"] = beneficiario.upper()
                    logger.info(f"✅ Beneficiário extraído: {extracted['issuer']}")
                    break
        
        if not extracted["issuer"]:
            logger.warning("❌ Beneficiário não encontrado")
        
        # Calcular confiança baseada nos campos ESSENCIAIS
        extracted["confidence"] = self._calculate_confidence(extracted)
        logger.info(f"📊 Confiança calculada: {extracted['confidence']:.2%} | Campos: amount={extracted['amount']}, due_date={extracted['due_date']}, issuer={extracted['issuer']}, barcode={'sim' if extracted['barcode'] else 'não'}")
        
        return extracted
    
    def _calculate_confidence(self, extracted: Dict[str, Any]) -> float:
        """
        Calcula confiança baseada apenas nos campos ESSENCIAIS extraídos.
        """
        has_amount = extracted.get("amount") is not None and extracted.get("amount") > 0
        has_due_date = extracted.get("due_date") is not None
        has_issuer = extracted.get("issuer") is not None and len(extracted.get("issuer", "")) >= 3
        has_barcode = extracted.get("barcode") is not None and len(extracted.get("barcode", "")) == 44
        
        # Confiança baseada em campos ESSENCIAIS
        if has_amount and has_due_date and has_barcode:
            # Todos os campos essenciais = confiança muito alta
            return 0.95 if has_issuer else 0.90
        elif has_amount and has_due_date:
            # Valor + data (mais importantes) = alta confiança
            return 0.85 if has_issuer else 0.80
        elif has_barcode and (has_amount or has_due_date):
            # Código de barras + um campo principal = boa confiança
            return 0.75
        elif has_amount or has_due_date:
            # Apenas um campo essencial = confiança média
            return 0.60 if has_issuer else 0.55
        elif has_barcode:
            # Apenas código de barras = confiança baixa-média
            return 0.50
        elif has_issuer:
            # Apenas beneficiário = confiança baixa
            return 0.40
        else:
            # Nada extraído = confiança muito baixa
            return 0.25
    
    def _empty_result(self, reason: str) -> Dict[str, Any]:
        """Retorna resultado vazio com motivo."""
        return {
            "issuer": None,
            "amount": None,
            "currency": "BRL",
            "due_date": None,
            "barcode": None,
            "payment_place": None,
            "confidence": 0.0,
            "notes": reason
        }


# Instância global
brazilian_bill_extractor = BrazilianBillExtractor()

