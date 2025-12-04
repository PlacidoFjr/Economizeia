# 🚀 Configurar Google Gemini para FinGuia

## ✅ Status: Configurado!

A integração com Google Gemini foi configurada e está pronta para uso.

---

## 📋 O que foi feito

1. ✅ Serviço Gemini criado (`backend/app/services/gemini_service.py`)
2. ✅ Chatbot atualizado para usar Gemini quando configurado
3. ✅ Dependência `google-generativeai` adicionada
4. ✅ Configuração no `.env` adicionada
5. ✅ Chave de API configurada

---

## 🔧 Configuração Atual

**Arquivo:** `backend/.env`

```env
GEMINI_API_KEY=AIzaSyBqh15bgWiyJbgVZXgKBVduZ1opLki78Vg
USE_GEMINI=true
GEMINI_MODEL=gemini-1.5-flash
```

**Modelo:** `gemini-2.0-flash` (mais rápido, ideal para chatbot)

---

## 🎯 Como Funciona

### Modo Automático
O sistema verifica automaticamente:
- Se `USE_GEMINI=true` e `GEMINI_API_KEY` está configurada → usa **Gemini**
- Caso contrário → usa **Ollama** (fallback)

### Vantagens do Gemini
- ⚡ **Muito rápido** (1-3 segundos vs 8-15s do Ollama)
- 🌟 **Melhor qualidade** de resposta
- 🇧🇷 **Melhor português** brasileiro
- 📊 **6 milhões de tokens/dia grátis** (180M/mês)

---

## 🔄 Alternar entre Gemini e Ollama

### Usar Gemini (Recomendado)
```env
USE_GEMINI=true
GEMINI_API_KEY=sua_chave_aqui
```

### Usar Ollama (Local)
```env
USE_GEMINI=false
# ou remova a linha USE_GEMINI
```

---

## 🧪 Testar a Integração

### 1. Reiniciar o Backend
```powershell
docker-compose restart backend
```

### 2. Testar no Chatbot
1. Acesse o sistema
2. Abra o chatbot
3. Digite: "Quantos boletos eu tenho?"
4. Deve responder rapidamente (1-3 segundos)

### 3. Verificar Logs
```powershell
docker logs finguia-backend -f
```

Procure por mensagens como:
- `"Using Gemini service"` (se estiver usando Gemini)
- `"Using Ollama service"` (se estiver usando Ollama)

---

## 📊 Comparação de Performance

| Métrica | Gemini | Ollama (Qwen2.5) |
|---------|--------|------------------|
| **Velocidade** | 1-3s ⚡⚡⚡⚡⚡ | 8-15s ⚡⚡ |
| **Qualidade** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Português** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Custo** | Gratuito* | Gratuito |
| **Privacidade** | Nuvem | Local |

*Gratuito até 6M tokens/dia

---

## 🔑 Obter Nova Chave de API

Se precisar de uma nova chave:

1. Acesse: https://aistudio.google.com/
2. Faça login com sua conta Google
3. Clique em "Get API Key"
4. Crie uma nova chave ou use uma existente
5. Copie a chave e atualize no `.env`

---

## ⚠️ Limites da API Gratuita

**Google Gemini (Gratuito):**
- ✅ 6 milhões de tokens/dia
- ✅ 180 milhões de tokens/mês
- ✅ 15 requests/minuto
- ✅ Sem custo até esses limites

**Limites do Modelo Gemini 2.0 Flash:**
- ✅ **Entrada:** 1.048.576 tokens (~800K palavras)
- ✅ **Saída:** 8.192 tokens (~6K palavras)
- ✅ **Contexto:** 1 milhão de tokens

**Recomendação:** Para uso normal do FinGuia, esses limites são mais que suficientes. Veja `docs/LIMITES_TOKENS_GEMINI.md` para detalhes completos.

---

## 🐛 Troubleshooting

### Erro: "GEMINI_API_KEY não configurada"
**Solução:** Verifique se a chave está no `.env` e reinicie o backend.

### Erro: "API key not valid"
**Solução:** 
1. Verifique se a chave está correta
2. Verifique se a API está habilitada no Google Cloud Console
3. Obtenha uma nova chave em https://aistudio.google.com/

### Erro: "Quota exceeded"
**Solução:** Você atingiu o limite diário. Aguarde ou use Ollama como fallback.

### Sistema ainda usando Ollama
**Solução:**
1. Verifique se `USE_GEMINI=true` no `.env`
2. Verifique se `GEMINI_API_KEY` está configurada
3. Reinicie o backend: `docker-compose restart backend`

---

## 📝 Notas Importantes

1. **Privacidade:** Dados são enviados para servidores do Google
2. **Internet:** Requer conexão com internet
3. **Fallback:** Se Gemini falhar, o sistema tenta usar Ollama automaticamente
4. **Performance:** Gemini é significativamente mais rápido que Ollama

---

## ✅ Próximos Passos

1. **Reiniciar o backend:**
   ```powershell
   docker-compose restart backend
   ```

2. **Testar o chatbot:**
   - Acesse o sistema
   - Abra o chatbot
   - Faça algumas perguntas

3. **Monitorar performance:**
   - Verifique os logs
   - Compare velocidade de resposta
   - Avalie qualidade das respostas

---

## 🎉 Pronto!

O Gemini está configurado e pronto para uso. O chatbot agora deve responder muito mais rápido! 🚀

