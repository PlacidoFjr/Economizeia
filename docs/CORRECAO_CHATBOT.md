# 🔧 Correção do Chatbot - Erro de Conexão com Ollama

## 🐛 Problema Identificado

O chatbot estava retornando erro: "Desculpe, ocorreu um erro ao processar sua mensagem"

**Causa:** O backend dentro do Docker não conseguia se conectar ao Ollama porque estava usando `http://localhost:11434`, mas dentro do container Docker, `localhost` se refere ao próprio container, não ao host.

---

## ✅ Correções Aplicadas

### 1. URL do Ollama no `.env`

**Antes:**
```env
OLLAMA_BASE_URL=http://localhost:11434
```

**Depois:**
```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

**Explicação:** `host.docker.internal` é um DNS especial do Docker que aponta para o host (sua máquina), permitindo que containers acessem serviços rodando no host.

### 2. Melhor Tratamento de Erros

Adicionado tratamento de erro mais amigável no chatbot:

- ✅ Se o Ollama não estiver disponível, o chatbot retorna uma mensagem útil explicando o problema
- ✅ Fornece informações sobre o que o assistente pode fazer
- ✅ Não retorna erro genérico, mas uma resposta útil

### 3. Import do Logger

Adicionado `import logging` e inicializado `logger` no arquivo `chatbot.py`.

---

## 🧪 Como Verificar se Está Funcionando

### 1. Verificar Configuração

```powershell
docker exec finguia-backend python -c "from app.core.config import settings; print('OLLAMA_BASE_URL:', settings.OLLAMA_BASE_URL)"
```

Deve mostrar: `OLLAMA_BASE_URL: http://host.docker.internal:11434`

### 2. Verificar Ollama

```powershell
curl http://localhost:11434/api/tags
```

Deve retornar a lista de modelos disponíveis.

### 3. Testar Chatbot

1. Acesse o sistema
2. Abra o chatbot
3. Digite: "o que você consegue fazer?"
4. Deve receber uma resposta do assistente

---

## 📋 Resposta de Fallback

Quando o Ollama não está disponível, o chatbot agora retorna:

```
Olá! Sou o assistente virtual do FinGuia. 

No momento, estou com dificuldades para me conectar ao servidor de IA. Mas posso ajudá-lo com algumas informações:

**O que posso fazer:**
• Ajudar você a entender como usar o sistema
• Explicar funcionalidades do FinGuia
• Orientar sobre upload de boletos
• Explicar como agendar pagamentos

**Para adicionar despesas via chat:**
Use comandos como:
• "Adicionar despesa de R$ 150,50 para energia elétrica"
• "Criar boleto de R$ 300,00 vencendo em 15/12/2024"

Por favor, verifique se o Ollama está rodando e tente novamente em alguns instantes.
```

---

## ⚠️ Importante

### Para Windows/Mac

`host.docker.internal` funciona automaticamente no Docker Desktop.

### Para Linux

Se `host.docker.internal` não funcionar, você pode:

1. **Opção 1:** Usar o IP da máquina host
   ```env
   OLLAMA_BASE_URL=http://172.17.0.1:11434
   ```

2. **Opção 2:** Adicionar `extra_hosts` no `docker-compose.yml`:
   ```yaml
   backend:
     extra_hosts:
       - "host.docker.internal:host-gateway"
   ```

---

## ✅ Status

**✅ CORRIGIDO!**

O chatbot agora:
- ✅ Conecta corretamente ao Ollama
- ✅ Retorna respostas úteis mesmo quando há problemas
- ✅ Tem melhor tratamento de erros

**Teste agora no sistema!** 🎉

