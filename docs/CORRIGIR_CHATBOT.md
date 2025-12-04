# 🔧 Como Corrigir o Chatbot - FinGuia

## 🔍 Problema Identificado

O chatbot não está funcionando porque o **Ollama não está rodando**. O sistema precisa do Ollama para processar as mensagens do chatbot.

## ✅ Soluções

### Opção 1: Rodar Ollama no Host (Recomendado para Desenvolvimento)

1. **Instalar Ollama:**
   - Baixe em: https://ollama.ai/download
   - Instale no Windows
   - Execute: `ollama serve` (ou inicie como serviço)

2. **Baixar o modelo:**
   ```bash
   ollama pull llama3.2
   ```

3. **Verificar se está rodando:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

4. **O docker-compose já está configurado** para usar `http://host.docker.internal:11434`

### Opção 2: Adicionar Ollama ao Docker Compose (Recomendado para Produção)

Adicionar o serviço Ollama ao `docker-compose.yml`:

```yaml
  ollama:
    image: ollama/ollama:latest
    container_name: finguia-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  ollama_data:
```

E atualizar o `OLLAMA_BASE_URL` no backend para:
```yaml
OLLAMA_BASE_URL: http://ollama:11434
```

## 🚀 Passos para Corrigir AGORA

### 1. Verificar se Ollama está rodando:
```powershell
curl http://localhost:11434/api/tags
```

### 2. Se não estiver rodando, instalar e iniciar:
- Baixar Ollama: https://ollama.ai/download
- Instalar
- Executar: `ollama serve`
- Baixar modelo: `ollama pull llama3.2`

### 3. Reiniciar o backend:
```powershell
docker restart finguia-backend
```

### 4. Testar o chatbot:
- Abrir o site
- Clicar no botão do chatbot
- Enviar uma mensagem

## 🔍 Verificar Logs

```powershell
# Ver logs do backend
docker logs finguia-backend --tail 50

# Verificar erros do Ollama
docker logs finguia-backend | Select-String "ollama\|Ollama\|OLLAMA"
```

## ⚠️ Erros Comuns

1. **"Connection refused"** → Ollama não está rodando
2. **"Timeout"** → Ollama está lento ou modelo não está baixado
3. **"Model not found"** → Modelo não foi baixado (`ollama pull llama3.2`)

## 📝 Nota

O chatbot funciona melhor com o Ollama rodando. Sem ele, o sistema retorna mensagens de fallback genéricas.

