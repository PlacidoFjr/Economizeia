# 🔍 Treinamento Customizado do OCR - Análise FinGuia

## 📊 Situação Atual do OCR

### Como Funciona Hoje
- ✅ **Tesseract OCR 5.5.0** instalado
- ✅ **Idioma Português** (`por`) disponível
- ✅ **Modelo pré-treinado** do Tesseract (não customizado)
- ✅ **Processamento:** Imagens → Tesseract → Texto bruto

### Fluxo Atual
```
Boleto (PDF/Imagem)
    ↓
Tesseract OCR (modelo padrão português)
    ↓
Texto extraído (com erros do OCR)
    ↓
Ollama corrige e estrutura os dados
```

---

## 🤔 Precisamos Treinar um Modelo Customizado?

### ❌ **NÃO PRECISAMOS** se:
- ✅ Tesseract padrão está extraindo texto razoavelmente bem
- ✅ Ollama está corrigindo erros do OCR
- ✅ Taxa de sucesso > 70% após correção do Ollama
- ✅ Erros são principalmente de formatação, não de reconhecimento

### ✅ **PRECISARÍAMOS** se:
- ❌ Taxa de erro muito alta mesmo após correção
- ❌ Erros sistemáticos que Ollama não consegue corrigir
- ❌ Formato específico de boletos que Tesseract não reconhece bem
- ❌ Fontes/estilos muito específicos que o modelo padrão não cobre

---

## 🎯 Estratégia Recomendada: **Melhorar Pré-processamento**

### Fase 1: Otimizar Pré-processamento (RECOMENDADO AGORA) ✅

**Por que é melhor que treinar modelo:**
- ✅ Rápido (implementar em horas)
- ✅ Não precisa de dados de treinamento
- ✅ Funciona com qualquer modelo
- ✅ Melhora resultados imediatamente

**Técnicas de Pré-processamento:**

#### 1. **Melhorar Qualidade da Imagem**
```python
def preprocess_image(image):
    # Converter para escala de cinza
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Reduzir ruído
    denoised = cv2.fastNlMeansDenoising(gray)
    
    # Aumentar contraste
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)
    
    # Binarização (preto e branco)
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary
```

#### 2. **Corrigir Inclinação (Deskew)**
```python
def deskew_image(image):
    # Detectar ângulo de rotação
    coords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    
    # Corrigir rotação
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    return rotated
```

#### 3. **Remover Bordas e Ruído**
```python
def remove_borders(image):
    # Remover bordas pretas
    contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
        cropped = image[y:y+h, x:x+w]
        return cropped
    return image
```

#### 4. **Ajustar Resolução**
```python
def optimize_resolution(image):
    # Tesseract funciona melhor com 300 DPI
    height, width = image.shape[:2]
    
    # Se muito pequeno, aumentar
    if height < 300 or width < 300:
        scale = 300 / min(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    
    # Se muito grande, reduzir (acelera processamento)
    elif height > 2000 or width > 2000:
        scale = 2000 / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    return image
```

### Fase 2: Configurar Tesseract Otimizado (FÁCIL)

**PSM (Page Segmentation Mode):**
- `--psm 6` - Assume bloco uniforme de texto (boletos)
- `--psm 11` - Texto esparso (boletos com muitos espaços)
- `--psm 12` - OCR com orientação detectada

**OEM (OCR Engine Mode):**
- `--oem 3` - Padrão (LSTM + Legacy)

**Configuração Recomendada:**
```python
custom_config = r'--oem 3 --psm 6 -l por'
pytesseract.image_to_string(image, config=custom_config, lang='por')
```

### Fase 3: Treinamento Customizado (SÓ SE NECESSÁRIO)

**Quando considerar:**
- Após otimizar pré-processamento
- Se ainda tiver problemas específicos
- Se formato de boletos for muito único

**Requisitos:**
- 100-500 imagens de boletos anotadas
- Ferramentas: `tesstrain` (Tesseract training tools)
- Tempo: 1-2 semanas
- Conhecimento: Treinamento de modelos OCR

---

## 📈 Comparação: Pré-processamento vs. Treinamento

| Aspecto | Pré-processamento | Treinamento Customizado |
|---------|------------------|------------------------|
| **Tempo** | Horas | Semanas |
| **Dados necessários** | Nenhum | 100-500 imagens anotadas |
| **Custo** | Baixo | Médio-Alto |
| **Complexidade** | Baixa | Alta |
| **Manutenção** | Fácil | Difícil |
| **Melhoria esperada** | 10-30% | 20-50% |
| **Recomendação** | ✅ **FAZER AGORA** | ⚠️ Só se necessário |

---

## 🎯 Recomendações Imediatas

### 1. **Implementar Pré-processamento** (Prioridade ALTA) ✅

**Benefícios:**
- Melhora qualidade do OCR imediatamente
- Reduz erros de reconhecimento
- Funciona com modelo padrão
- Fácil de implementar

### 2. **Otimizar Configuração do Tesseract** (Prioridade MÉDIA)

**Ações:**
- Testar diferentes PSM modes
- Ajustar para formato de boletos
- Usar configuração específica por tipo

### 3. **Melhorar Correção Pós-OCR** (Prioridade ALTA)

**Ações:**
- Ollama já faz isso, mas podemos melhorar
- Adicionar regras específicas para boletos
- Corrigir erros comuns (R0$ → R$, etc.)

### 4. **Coletar Métricas** (Prioridade BAIXA)

**Ações:**
- Medir taxa de erro do OCR
- Identificar padrões de erro
- Decidir se precisa treinar modelo

---

## 🔧 Implementação: Melhorar OCR Agora

### O que podemos fazer AGORA:

1. ✅ **Adicionar pré-processamento de imagens**
2. ✅ **Otimizar configuração do Tesseract**
3. ✅ **Melhorar tratamento de PDFs**
4. ✅ **Adicionar validações pós-OCR**

### Código de Exemplo:
```python
def extract_text_from_image_improved(self, image_bytes: bytes) -> Tuple[str, float]:
    """Extract text with improved preprocessing."""
    try:
        # Carregar imagem
        image = Image.open(io.BytesIO(image_bytes))
        img_array = np.array(image)
        
        # Pré-processar
        processed = preprocess_image(img_array)
        processed = deskew_image(processed)
        processed = remove_borders(processed)
        processed = optimize_resolution(processed)
        
        # Converter de volta para PIL
        processed_image = Image.fromarray(processed)
        
        # OCR com configuração otimizada
        custom_config = r'--oem 3 --psm 6 -l por'
        data = pytesseract.image_to_data(
            processed_image, 
            lang='por', 
            config=custom_config,
            output_type=pytesseract.Output.DICT
        )
        
        # Processar resultado...
        ...
```

---

## 📊 Métricas para Avaliar

### Antes de Considerar Treinamento:
1. **Taxa de Erro do OCR:** < 15%?
2. **Taxa de Sucesso após Ollama:** > 80%?
3. **Campos extraídos corretamente:**
   - Emissor: > 85%?
   - Valor: > 95%?
   - Data: > 90%?
4. **Confiança média:** > 0.7?

### Se métricas forem boas:
✅ **NÃO precisa treinar modelo!**
✅ Continue melhorando pré-processamento

### Se métricas forem ruins:
⚠️ **Considerar treinamento**
⚠️ Mas primeiro: melhorar pré-processamento

---

## ✅ Conclusão

### **NÃO precisamos treinar modelo OCR AGORA** porque:

1. ✅ Tesseract padrão português já é bom
2. ✅ Pré-processamento pode melhorar muito
3. ✅ Ollama corrige erros do OCR
4. ✅ Treinamento é complexo e demorado

### **O que fazer:**
1. ✅ Implementar pré-processamento de imagens
2. ✅ Otimizar configuração do Tesseract
3. ✅ Melhorar correção pós-OCR
4. ✅ Coletar métricas
5. ⚠️ Só considerar treinamento se métricas não melhorarem

### **Quando considerar treinamento:**
- Após otimizar pré-processamento por 1-2 meses
- Se taxa de erro ainda estiver > 20%
- Se tivermos 100+ boletos anotados
- Se formato específico não for reconhecido

---

## 🚀 Próximos Passos Recomendados

1. **Implementar pré-processamento** (esta semana)
2. **Otimizar configuração Tesseract** (esta semana)
3. **Coletar métricas** (próximas semanas)
4. **Avaliar necessidade de treinamento** (após 1-2 meses)

**Resumo:** Foque em melhorar pré-processamento primeiro. Treinamento customizado só se realmente necessário após otimizar pré-processamento.

