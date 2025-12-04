# 🔍 Diagnóstico Completo do Timeout do Chatbot

## 📊 Situação Atual

### Problema Observado:
- Chatbot está dando **timeout** mesmo após otimizações
- Mostra dados zerados (0 boletos, R$ 0.00) quando há timeout
- Ollama responde em ~7s para testes simples, mas timeout em requisições reais

## 🔍 Análise Detalhada

### 1. **Ollama está Funcionando** ✅
- Teste direto: **7 segundos** para resposta simples
- Status: Ollama rodando e respondendo
- Modelo `qwen2.5:7b` disponível

### 2. **Problema: Contexto + Modelo Lento** ⚠️

**Causas Identificadas:**

1. **Modelo Qwen2.5:7b é mais lento** que Llama3.2
   - Qwen2.5:7b tem 7.6B parâmetros (maior)
   - Processa mais devagar que modelos menores
   - Melhor qualidade, mas mais lento

2. **Contexto ainda pode ser grande**
   - Mesmo otimizado, com muitos boletos o contexto cresce
   - Histórico de conversa adiciona tokens
   - System prompt também consome tokens

3. **Conexão Docker → Host**
   - `host.docker.internal:11434` pode ter latência
   - Windows pode ter problemas com essa conexão
   - Network overhead entre containers

## ✅ Otimizações Aplicadas

### 1. **Contexto Ultra Compacto**
- Formato minimalista (sem emojis desnecessários)
- Apenas dados essenciais
- Máximo 3 itens por lista

### 2. **Configuração Mais Agressiva**
- **num_predict**: 200 → **150** (respostas mais curtas)
- **num_ctx**: 2048 → **1536** (menos contexto para processar)
- **timeout**: 30s → **25s** (mais realista)

### 3. **System Prompt Reduzido**
- Removidas instruções redundantes
- Prompt mais direto e conciso
- Foco em usar dados reais

### 4. **Logs de Debug**
- Adicionados logs para monitorar requisições
- Medir tamanho do contexto
- Identificar gargalos

## 🎯 Próximos Passos (Se Ainda Houver Timeout)

### Opção 1: Usar Modelo Mais Rápido
```python
OLLAMA_MODEL = "llama3.2:latest"  # Mais rápido (3.2B vs 7.6B)
```

### Opção 2: Implementar Cache
- Cachear respostas para perguntas comuns
- Reduzir chamadas ao Ollama

### Opção 3: Streaming
- Usar `stream: true` para respostas incrementais
- Usuário vê resposta aparecendo aos poucos

### Opção 4: Respostas Híbridas
- Dados reais sempre disponíveis (sem Ollama)
- Ollama apenas para análises complexas

## 📝 Verificações Necessárias

1. **Verificar se usuário tem boletos:**
   - Dados zerados podem ser reais (usuário novo)
   - Ou problema na query do banco

2. **Testar conexão Docker → Ollama:**
   ```powershell
   docker exec finguia-backend curl http://host.docker.internal:11434/api/tags
   ```

3. **Monitorar logs em tempo real:**
   ```powershell
   docker logs -f finguia-backend | Select-String "ollama|timeout"
   ```

## ✅ Status Atual

**Otimizações aplicadas:**
- ✅ Contexto ultra compacto
- ✅ Configuração mais agressiva
- ✅ System prompt reduzido
- ✅ Logs de debug
- ✅ Timeout ajustado

**Resultado esperado:**
- Respostas em **10-20 segundos** (antes: timeout)
- Dados reais sempre mostrados (mesmo em timeout)

## 🧪 Teste Agora

1. Enviar mensagem simples: "Quantos boletos eu tenho?"
2. Verificar logs: `docker logs finguia-backend --tail 20`
3. Se ainda timeout, considerar trocar para modelo mais rápido

