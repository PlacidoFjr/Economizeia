# Guia: Treinar Tesseract para Boletos Brasileiros

## 📋 Visão Geral

Este guia explica como melhorar a extração de texto de boletos brasileiros usando Tesseract OCR com modelos customizados.

## 🎯 Por que treinar?

Boletos brasileiros têm características específicas:
- Layout padronizado (FEBRABAN)
- Fontes específicas (OCR-B, código de barras)
- Campos fixos (valor, vencimento, beneficiário, código de barras)
- Formatação específica (datas DD/MM/AAAA, valores R$)

## 📚 Opções de Treinamento

### Opção 1: Usar Modelo Pré-treinado (Recomendado)

O Tesseract já vem com modelo português (`por`) que funciona bem para boletos:

```bash
# Instalar Tesseract com suporte a português
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-por

# Windows (via Chocolatey):
choco install tesseract --params '/Languages:por'

# Verificar modelos instalados
tesseract --list-langs
```

**No código Python:**
```python
import pytesseract

# Usar modelo português
text = pytesseract.image_to_string(image, lang='por')
```

### Opção 2: Treinar Modelo Customizado (Avançado)

#### Passo 1: Coletar Amostras

1. **Coletar 50-100 boletos reais** (diferentes bancos, formatos)
2. **Variar condições:**
   - Boletos escaneados vs. fotos
   - Diferentes qualidades de imagem
   - Diferentes bancos (Banco do Brasil, Itaú, Bradesco, etc.)

#### Passo 2: Preparar Dados de Treinamento

**Estrutura de diretórios:**
```
training_data/
├── images/          # Imagens dos boletos
│   ├── boleto_001.png
│   ├── boleto_002.png
│   └── ...
├── ground_truth/    # Texto correto extraído manualmente
│   ├── boleto_001.txt
│   ├── boleto_002.txt
│   └── ...
└── output/          # Modelo treinado gerado
```

**Formato do ground_truth (boleto_001.txt):**
```
BANCO DO BRASIL S.A.
AGENCIA: 1234-5
CONTA CORRENTE: 12345-6
BENEFICIARIO: EMPRESA XYZ LTDA
CNPJ: 12.345.678/0001-90
VALOR DO DOCUMENTO: R$ 1.234,56
VENCIMENTO: 15/12/2024
NOSSO NUMERO: 12345678901234567890
CODIGO DE BARRAS: 00190500954014481606906809350314337370000000100
```

#### Passo 3: Criar Arquivos .box

O arquivo `.box` mapeia cada caractere na imagem:

```bash
# Gerar arquivos .box automaticamente
tesseract boleto_001.png boleto_001 -l por batch.nochop makebox
```

**Formato do arquivo .box:**
```
B 10 20 30 40 0
A 30 20 50 40 0
N 50 20 70 40 0
C 70 20 90 40 0
O 90 20 110 40 0
```

#### Passo 4: Corrigir Arquivos .box

Use ferramentas como:
- **jTessBoxEditor** (Windows/Java): https://github.com/nguyenq/jTessBoxEditor
- **QT Box Editor**: https://github.com/zdenop/qt-box-editor

#### Passo 5: Treinar o Modelo

```bash
# 1. Criar arquivo de fontes
echo "BoletoBrasil 0 0 0 0 0" > font_properties

# 2. Gerar arquivos de treinamento
tesseract boleto_001.png boleto_001 -l por nobatch box.train

# 3. Extrair características
unicharset_extractor *.box

# 4. Criar arquivo de unicharset
shapeclustering -F font_properties -U unicharset *.tr

# 5. Gerar arquivo de clustering
mftraining -F font_properties -U unicharset -O unicharset *.tr

# 6. Gerar arquivo de clustering de formas
cntraining *.tr

# 7. Renomear arquivos
mv inttemp boleto_brasil.inttemp
mv normproto boleto_brasil.normproto
mv pffmtable boleto_brasil.pffmtable
mv shapetable boleto_brasil.shapetable
mv unicharset boleto_brasil.unicharset

# 8. Combinar arquivos
combine_tessdata boleto_brasil.

# 9. Copiar modelo treinado
sudo cp boleto_brasil.traineddata /usr/share/tesseract-ocr/5/tessdata/
```

#### Passo 6: Usar Modelo Customizado

```python
import pytesseract

# Usar modelo customizado
text = pytesseract.image_to_string(image, lang='boleto_brasil')
```

## 🔧 Melhorias Práticas (Sem Treinamento)

### 1. Pré-processamento de Imagem

```python
from PIL import Image
import cv2
import numpy as np

def preprocess_bill_image(image_path):
    """Melhora qualidade da imagem antes do OCR."""
    # Ler imagem
    img = cv2.imread(image_path)
    
    # Converter para escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Aplicar threshold (binarização)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Reduzir ruído
    denoised = cv2.fastNlMeansDenoising(thresh, h=10)
    
    # Aumentar contraste
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)
    
    # Redimensionar se muito pequeno (melhora OCR)
    height, width = enhanced.shape
    if height < 1000:
        scale = 1000 / height
        enhanced = cv2.resize(enhanced, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    return enhanced
```

### 2. Configuração Otimizada do Tesseract

```python
import pytesseract

# Configuração para boletos brasileiros
custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,/-:R$ '

text = pytesseract.image_to_string(
    image,
    lang='por',
    config=custom_config
)
```

**Explicação dos parâmetros:**
- `--oem 3`: Usar LSTM OCR Engine (mais preciso)
- `--psm 6`: Assumir bloco único de texto uniforme
- `tessedit_char_whitelist`: Limitar caracteres esperados (melhora precisão)

### 3. Extração de Regiões Específicas

```python
def extract_bill_regions(image):
    """Extrai regiões específicas do boleto."""
    height, width = image.shape[:2]
    
    regions = {
        'top': image[0:height//3, 0:width],      # Cabeçalho (banco, agência)
        'middle': image[height//3:2*height//3, 0:width],  # Dados do beneficiário
        'bottom': image[2*height//3:height, 0:width],    # Código de barras
    }
    
    extracted = {}
    for region_name, region_img in regions.items():
        text = pytesseract.image_to_string(region_img, lang='por')
        extracted[region_name] = text
    
    return extracted
```

### 4. Pós-processamento com Regex

```python
import re

def extract_bill_fields(ocr_text):
    """Extrai campos específicos usando regex."""
    fields = {}
    
    # Valor (R$ 1.234,56 ou R$1234,56)
    valor_match = re.search(r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', ocr_text)
    if valor_match:
        valor_str = valor_match.group(1).replace('.', '').replace(',', '.')
        fields['amount'] = float(valor_str)
    
    # Data de vencimento (DD/MM/AAAA)
    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', ocr_text)
    if date_match:
        fields['due_date'] = date_match.group(1)
    
    # Código de barras (44 dígitos)
    barcode_match = re.search(r'(\d{44})', ocr_text)
    if barcode_match:
        fields['barcode'] = barcode_match.group(1)
    
    # CNPJ (XX.XXX.XXX/XXXX-XX)
    cnpj_match = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', ocr_text)
    if cnpj_match:
        fields['cnpj'] = cnpj_match.group(1)
    
    return fields
```

## 🚀 Implementação no Projeto

### Atualizar `ocr_service.py`:

```python
def extract_text(self, file_bytes: bytes, content_type: str) -> tuple[str, float]:
    """Extrai texto com pré-processamento otimizado."""
    # Pré-processar imagem
    processed_image = self._preprocess_image(file_bytes, content_type)
    
    # Configuração otimizada
    config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,/-:R$ '
    
    # Extrair texto
    text = pytesseract.image_to_string(
        processed_image,
        lang='por',
        config=config
    )
    
    # Calcular confiança (simulado - Tesseract não retorna confiança por padrão)
    confidence = self._estimate_confidence(text)
    
    return text, confidence
```

## 📊 Comparação: Modelo Padrão vs. Customizado

| Aspecto | Modelo Padrão (`por`) | Modelo Customizado |
|---------|----------------------|-------------------|
| **Tempo de setup** | Imediato | 2-4 semanas |
| **Precisão geral** | 85-90% | 92-97% |
| **Manutenção** | Automática | Manual |
| **Custo** | Grátis | Tempo de desenvolvimento |

## 💡 Recomendação

**Para este projeto, recomendo:**

1. **Usar modelo `por` pré-treinado** (já instalado)
2. **Implementar pré-processamento de imagem** (melhora 10-15%)
3. **Usar regex para extrair campos específicos** (mais confiável)
4. **Combinar OCR + AI (Ollama/Gemini)** para interpretação (já implementado)

O treinamento customizado só é necessário se:
- Precisão atual < 80%
- Boletos muito específicos (formato não padrão)
- Requisitos de precisão > 95%

## 🔗 Recursos

- **Tesseract Training Docs**: https://tesseract-ocr.github.io/tessdoc/TrainingTesseract-4.00.html
- **jTessBoxEditor**: https://github.com/nguyenq/jTessBoxEditor
- **FEBRABAN Layout**: https://febraban.org.br/
- **Tesseract PSM Modes**: https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html#page-segmentation-method

