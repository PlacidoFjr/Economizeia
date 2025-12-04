# 🔧 Troubleshooting - Problemas com Ollama

## Erro: "bind: Normalmente é permitida apenas uma utilização de cada endereço de soquete (protocolo/endereço de rede/porta)"

### O que significa?

Este erro acontece quando você tenta iniciar o Ollama, mas ele já está rodando em outro processo ou terminal.

A porta 11434 (porta padrão do Ollama) já está sendo usada por outra instância do Ollama.

---

## ✅ Solução Rápida (Mais Comum)

**Na maioria dos casos, o Ollama JÁ ESTÁ RODANDO!**

### Verificar se está rodando:

```bash
ollama list
```

**Se funcionar** (mostrar a lista de modelos):
- ✅ O Ollama já está rodando!
- ✅ Você não precisa fazer nada
- ✅ Pode continuar usando normalmente

**Se não funcionar** (erro de conexão):
- O Ollama não está rodando
- Continue com as soluções abaixo

---

## 🔍 Soluções Detalhadas

### Solução 1: Encontrar e Parar o Processo Existente

#### Windows:

**Opção A - Gerenciador de Tarefas:**
1. Pressione `Ctrl + Shift + Esc` para abrir o Gerenciador de Tarefas
2. Vá na aba "Processos" ou "Detalhes"
3. Procure por "ollama" ou "ollama.exe"
4. Clique com botão direito > "Finalizar tarefa"
5. Confirme se necessário

**Opção B - Prompt de Comando:**
```cmd
# Encontrar o processo
netstat -ano | findstr :11434

# Você verá algo como:
# TCP    127.0.0.1:11434    0.0.0.0:0    LISTENING    12345
# O último número (12345) é o PID

# Parar o processo (substitua 12345 pelo PID que apareceu)
taskkill /PID 12345 /F
```

**Opção C - PowerShell:**
```powershell
# Encontrar e parar
Get-Process -Name ollama -ErrorAction SilentlyContinue | Stop-Process -Force
```

#### Mac:

```bash
# Encontrar o processo
lsof -i :11434

# Você verá algo como:
# ollama  12345  usuario  ...  TCP localhost:11434 (LISTEN)
# O número 12345 é o PID

# Parar o processo
kill 12345

# Se não funcionar, force:
kill -9 12345
```

#### Linux:

```bash
# Encontrar o processo
sudo lsof -i :11434
# ou
sudo netstat -tlnp | grep 11434
# ou
ps aux | grep ollama

# Parar o processo (substitua 12345 pelo PID)
kill 12345

# Se não funcionar, force:
kill -9 12345
```

---

### Solução 2: Reiniciar o Ollama

Depois de parar o processo, inicie novamente:

```bash
ollama serve
```

**Importante:** Deixe este terminal aberto enquanto usar o FinGuia!

---

### Solução 3: Usar Outra Porta (Avançado)

Se você realmente precisa rodar duas instâncias do Ollama:

1. **Inicie o Ollama em outra porta:**
   ```bash
   OLLAMA_HOST=127.0.0.1:11435 ollama serve
   ```

2. **Atualize o arquivo `.env`:**
   ```
   OLLAMA_BASE_URL=http://localhost:11435
   ```

3. **Reinicie os serviços Docker:**
   ```bash
   docker-compose restart backend celery-worker
   ```

---

## 🔄 Verificar se Está Funcionando

### Teste 1: Listar modelos
```bash
ollama list
```
Deve mostrar seus modelos instalados (ex: `llama3.2`)

### Teste 2: Testar API
```bash
curl http://localhost:11434/api/tags
```
Deve retornar JSON com a lista de modelos

### Teste 3: Teste simples
```bash
ollama run llama3.2 "Olá, como você está?"
```
Deve responder (pode demorar alguns segundos)

---

## 🐳 Ollama com Docker

Se você está usando Docker e o Ollama está rodando localmente:

### Configuração no `.env`:

**Windows:**
```
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

**Mac/Linux:**
```
OLLAMA_BASE_URL=http://host.docker.internal:11434
# ou se não funcionar:
OLLAMA_BASE_URL=http://172.17.0.1:11434
```

### Verificar se o Docker consegue acessar:

```bash
docker exec -it finguia-backend curl http://host.docker.internal:11434/api/tags
```

Se não funcionar, tente:
```bash
# No Windows, adicione ao hosts (C:\Windows\System32\drivers\etc\hosts):
# 127.0.0.1 host.docker.internal
```

---

## 📋 Checklist de Diagnóstico

Use este checklist para identificar o problema:

- [ ] O Ollama está instalado?
  ```bash
  ollama --version
  ```

- [ ] O modelo está instalado?
  ```bash
  ollama list
  ```

- [ ] O Ollama está rodando?
  ```bash
  ollama list
  # Se funcionar, está rodando
  ```

- [ ] A porta 11434 está livre?
  ```bash
  # Windows
  netstat -ano | findstr :11434
  
  # Mac/Linux
  lsof -i :11434
  ```

- [ ] O Docker consegue acessar o Ollama?
  ```bash
  docker exec -it finguia-backend curl http://host.docker.internal:11434/api/tags
  ```

- [ ] O arquivo `.env` está configurado corretamente?
  ```
  OLLAMA_BASE_URL=http://localhost:11434
  # ou
  OLLAMA_BASE_URL=http://host.docker.internal:11434
  ```

---

## 🚨 Problemas Comuns

### Problema: "Connection refused"

**Causa:** Ollama não está rodando

**Solução:**
```bash
ollama serve
```

### Problema: "Model not found"

**Causa:** Modelo não está instalado

**Solução:**
```bash
ollama pull llama3.2
```

### Problema: Docker não consegue acessar Ollama local

**Causa:** Configuração de rede

**Solução:**
1. Verifique o `.env`: `OLLAMA_BASE_URL=http://host.docker.internal:11434`
2. No Windows, pode precisar adicionar ao hosts
3. Tente usar o IP da máquina host diretamente

### Problema: Ollama muito lento

**Causa:** Modelo muito grande ou hardware insuficiente

**Solução:**
1. Use um modelo menor: `ollama pull llama3.2:1b` (versão 1 bilhão de parâmetros)
2. Feche outros programas pesados
3. Considere usar Ollama em servidor remoto mais potente

---

## 💡 Dicas

1. **Deixe o Ollama rodando:** Não precisa fechar o terminal onde está rodando `ollama serve`

2. **Use um terminal separado:** Deixe o Ollama rodando em um terminal e use outro para o FinGuia

3. **Verifique antes de iniciar:** Sempre use `ollama list` para verificar se já está rodando

4. **Logs do Ollama:** Se tiver problemas, veja os logs no terminal onde está rodando `ollama serve`

5. **Reinicie se necessário:** Se o Ollama travar, simplesmente pare (Ctrl+C) e inicie novamente

---

## 📞 Ainda com Problemas?

Se nada funcionar:

1. **Reinstale o Ollama:**
   - Desinstale completamente
   - Baixe e instale novamente
   - Baixe o modelo novamente: `ollama pull llama3.2`

2. **Verifique firewall:**
   - Windows: Verifique se o Firewall não está bloqueando
   - Mac: Verifique Preferências do Sistema > Segurança

3. **Verifique permissões:**
   - Certifique-se de ter permissões para usar a porta 11434
   - No Linux, pode precisar de `sudo` (não recomendado)

4. **Use Ollama em servidor remoto:**
   - Configure um servidor Ollama separado
   - Atualize `OLLAMA_BASE_URL` no `.env` com o IP do servidor

---

**Lembre-se:** Na maioria dos casos, o Ollama já está rodando e você só precisa verificar! ✅

