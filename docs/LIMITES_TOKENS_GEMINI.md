# 📊 Limites de Tokens - Gemini 2.0 Flash

## 🎯 Resumo Executivo

**Gemini 2.0 Flash** tem limites generosos que são mais que suficientes para o FinGuia:

- ✅ **Entrada:** 1.048.576 tokens (~800.000 palavras)
- ✅ **Saída:** 8.192 tokens (~6.000 palavras)
- ✅ **API Gratuita:** 6 milhões de tokens/dia (180M/mês)

---

## 📈 Limites do Modelo Gemini 2.0 Flash

### **Tokens de Entrada (Input)**
- **Limite:** 1.048.576 tokens
- **Equivalente:** ~800.000 palavras em português
- **Uso no FinGuia:** Contexto financeiro do usuário (boletos, categorias, histórico)
- **Status:** ✅ Mais que suficiente para nosso caso

### **Tokens de Saída (Output)**
- **Limite:** 8.192 tokens
- **Equivalente:** ~6.000 palavras em português
- **Uso no FinGuia:** Respostas do chatbot
- **Status:** ✅ Mais que suficiente para respostas detalhadas

### **Contexto Total**
- **Janela de Contexto:** 1 milhão de tokens
- **Permite:** Manter histórico de conversas extensas
- **Uso no FinGuia:** Histórico de até 10 mensagens anteriores

---

## 💰 Limites da API Gratuita (Google AI Studio)

### **Plano Gratuito**
- ✅ **6 milhões de tokens/dia**
- ✅ **180 milhões de tokens/mês**
- ✅ **15 requests/minuto**
- ✅ **Sem custo até esses limites**

### **O que isso significa na prática?**

#### **Cenário 1: Uso Normal do FinGuia**
- **Mensagens por dia:** ~50-100
- **Tokens por mensagem:** ~500-1000 (entrada + saída)
- **Total estimado:** 25.000 - 100.000 tokens/dia
- **Status:** ✅ **Muito abaixo do limite** (6M tokens/dia)

#### **Cenário 2: Uso Intensivo**
- **Mensagens por dia:** ~500
- **Tokens por mensagem:** ~2000
- **Total estimado:** 1.000.000 tokens/dia
- **Status:** ✅ **Ainda dentro do limite** (6M tokens/dia)

#### **Cenário 3: Uso Extremo**
- **Mensagens por dia:** ~3000
- **Tokens por mensagem:** ~2000
- **Total estimado:** 6.000.000 tokens/dia
- **Status:** ⚠️ **No limite** (6M tokens/dia)

---

## 📊 Comparação: Gemini 2.0 vs Outros Modelos

| Modelo | Entrada | Saída | Contexto | API Gratuita |
|--------|---------|-------|-----------|--------------|
| **Gemini 2.0 Flash** | 1M tokens | 8K tokens | 1M tokens | 6M/dia |
| Gemini 1.5 Pro | 2M tokens | 8K tokens | 2M tokens | 6M/dia |
| GPT-4o | 128K tokens | 16K tokens | 128K tokens | $0 (pago) |
| Claude 3.5 Sonnet | 200K tokens | 8K tokens | 200K tokens | $0 (pago) |

**Conclusão:** Gemini 2.0 Flash tem limites excelentes, especialmente para uso gratuito!

---

## 💡 Estimativa de Uso no FinGuia

### **Por Mensagem do Chatbot:**

#### **Entrada (Input):**
- Prompt do sistema: ~500 tokens
- Contexto financeiro: ~200-500 tokens
- Histórico de conversa: ~100-300 tokens
- Mensagem do usuário: ~50-200 tokens
- **Total por mensagem:** ~850-1.500 tokens

#### **Saída (Output):**
- Resposta do assistente: ~200-800 tokens
- **Total por resposta:** ~200-800 tokens

#### **Total por Interação:**
- **Entrada + Saída:** ~1.050-2.300 tokens por interação

### **Uso Diário Estimado:**

| Cenário | Mensagens/Dia | Tokens/Dia | % do Limite |
|---------|---------------|------------|-------------|
| **Leve** | 20 | ~40.000 | 0.67% |
| **Normal** | 100 | ~200.000 | 3.33% |
| **Intensivo** | 500 | ~1.000.000 | 16.67% |
| **Extremo** | 3.000 | ~6.000.000 | 100% |

**Conclusão:** Mesmo com uso intenso, você está bem abaixo do limite!

---

## 🔍 Como Monitorar o Uso

### **1. Verificar no Google AI Studio**
1. Acesse: https://aistudio.google.com/
2. Vá em "Usage" ou "Quotas"
3. Veja tokens usados hoje/mês

### **2. Adicionar Logging no Código** (Opcional)
```python
# Em gemini_service.py, adicionar:
logger.info(f"Tokens usados: entrada={input_tokens}, saída={output_tokens}")
```

### **3. Verificar Logs do Backend**
```powershell
docker logs finguia-backend | Select-String -Pattern "token|Token"
```

---

## ⚠️ O que Acontece se Exceder o Limite?

### **Limite Diário (6M tokens):**
- ⚠️ API retorna erro `429 Too Many Requests`
- ✅ Sistema automaticamente usa **Ollama como fallback**
- ✅ Usuário não percebe interrupção

### **Limite de Rate (15 req/min):**
- ⚠️ API retorna erro `429 Rate Limit Exceeded`
- ✅ Sistema aguarda e tenta novamente
- ✅ Se falhar, usa **Ollama como fallback**

### **Limite do Modelo (1M entrada, 8K saída):**
- ⚠️ API retorna erro `400 Bad Request`
- ✅ Sistema reduz contexto automaticamente
- ✅ Remove histórico antigo se necessário

---

## 🎯 Recomendações para Otimização

### **1. Reduzir Tamanho do Contexto**
```python
# Limitar histórico a 5 mensagens (ao invés de 10)
conversation_history[-5:]
```

### **2. Resumir Dados Financeiros**
```python
# Ao invés de listar todos os boletos, mostrar apenas:
# - Top 5 categorias
# - Top 5 emissores
# - Próximos 5 vencimentos
```

### **3. Cache de Respostas**
```python
# Cachear respostas frequentes (ex: "Quantos boletos tenho?")
# Reduz uso de tokens para perguntas repetidas
```

### **4. Usar Ollama para Tarefas Simples**
```python
# Usar Ollama para extração de despesas (menos tokens)
# Usar Gemini apenas para chat complexo
```

---

## 📈 Projeção de Custos (se Exceder Limite Gratuito)

### **Google Gemini Pricing (Pago):**
- **Gemini 2.0 Flash:** $0.075 por 1M tokens de entrada, $0.30 por 1M tokens de saída
- **Exemplo:** 10M tokens/dia = ~$0.75-3.00/dia = ~$22.50-90/mês

### **Comparação:**
- **Gratuito:** 6M tokens/dia = **$0/mês**
- **Pago (10M/dia):** ~$22.50-90/mês
- **Ollama (local):** **$0/mês** (sem limites)

**Recomendação:** Use o plano gratuito até precisar de mais. Para uso normal do FinGuia, o limite gratuito é mais que suficiente!

---

## ✅ Conclusão

### **Para o FinGuia:**
- ✅ **Limites do modelo:** Mais que suficientes
- ✅ **Limite da API gratuita:** Muito generoso (6M/dia)
- ✅ **Uso estimado:** 0.67% - 16.67% do limite diário
- ✅ **Fallback automático:** Ollama se exceder limite
- ✅ **Custo:** $0/mês para uso normal

### **Recomendação Final:**
**Não se preocupe com tokens!** O limite gratuito do Gemini é muito generoso para o uso normal do FinGuia. Mesmo com uso intenso, você estará bem abaixo do limite.

---

## 📝 Resumo Rápido

| Item | Valor | Status |
|------|-------|--------|
| **Tokens de Entrada** | 1.048.576 | ✅ Excelente |
| **Tokens de Saída** | 8.192 | ✅ Excelente |
| **API Gratuita/Dia** | 6.000.000 | ✅ Muito Generoso |
| **API Gratuita/Mês** | 180.000.000 | ✅ Muito Generoso |
| **Uso Estimado/Dia** | 40K - 1M | ✅ Bem Abaixo |
| **Custo** | $0 | ✅ Gratuito |

**🎉 Você está coberto!** O Gemini 2.0 Flash tem limites excelentes e o plano gratuito é mais que suficiente para o FinGuia.

