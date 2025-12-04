# 🚀 Guia Passo a Passo - FinGuia (Para Iniciantes)

Este guia vai te ajudar a configurar e rodar o FinGuia do zero, mesmo se você nunca trabalhou com essas ferramentas antes.

---

## 📋 O QUE VOCÊ VAI PRECISAR

Antes de começar, você precisa ter instalado no seu computador:

1. **Docker Desktop** - Para rodar os serviços
2. **Python 3.11 ou superior** - Para o backend
3. **Node.js 18 ou superior** - Para o frontend
4. **Ollama** - Para processamento de IA
5. **Git** (opcional) - Para clonar o projeto

---

## PASSO 1: INSTALAR O DOCKER DESKTOP

### O que é Docker?
Docker é uma ferramenta que permite rodar vários programas (como banco de dados, servidor web) de forma isolada, sem precisar instalar cada um separadamente.

### Como instalar:

1. **Windows/Mac:**
   - Acesse: https://www.docker.com/products/docker-desktop
   - Baixe o Docker Desktop
   - Instale e abra o programa
   - Aguarde ele inicializar (pode demorar alguns minutos na primeira vez)

2. **Linux:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install docker.io docker-compose
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

### Verificar se funcionou:
Abra um terminal (Prompt de Comando no Windows, Terminal no Mac/Linux) e digite:
```bash
docker --version
```
Se aparecer uma versão (ex: `Docker version 24.0.0`), está funcionando! ✅

---

## PASSO 2: INSTALAR O PYTHON

### O que é Python?
Python é a linguagem de programação usada no backend do FinGuia.

### Como instalar:

1. **Windows:**
   - Acesse: https://www.python.org/downloads/
   - Baixe a versão mais recente (3.11 ou superior)
   - **IMPORTANTE:** Durante a instalação, marque a opção "Add Python to PATH"
   - Instale normalmente

2. **Mac:**
   ```bash
   # Usando Homebrew (se tiver instalado)
   brew install python@3.11
   ```

3. **Linux:**
   ```bash
   sudo apt-get update
   sudo apt-get install python3.11 python3-pip
   ```

### Verificar se funcionou:
Abra um terminal e digite:
```bash
python --version
```
ou
```bash
python3 --version
```
Se aparecer algo como `Python 3.11.5`, está funcionando! ✅

---

## PASSO 3: INSTALAR O NODE.JS

### O que é Node.js?
Node.js é necessário para rodar o frontend (a parte visual) do FinGuia.

### Como instalar:

1. **Windows/Mac:**
   - Acesse: https://nodejs.org/
   - Baixe a versão LTS (Long Term Support)
   - Instale normalmente

2. **Linux:**
   ```bash
   # Ubuntu/Debian
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

### Verificar se funcionou:
Abra um terminal e digite:
```bash
node --version
npm --version
```
Se aparecerem versões (ex: `v18.17.0` e `9.6.7`), está funcionando! ✅

---

## PASSO 4: INSTALAR O OLLAMA

### O que é Ollama?
Ollama é o programa que faz a "inteligência artificial" do FinGuia, extraindo informações dos boletos.

### Como instalar:

1. **Windows:**
   - Acesse: https://ollama.ai/download
   - Baixe o instalador para Windows
   - Instale normalmente
   - Abra o Ollama (ele vai abrir uma janela do terminal)

2. **Mac:**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

3. **Linux:**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

### Baixar o modelo de IA:
Depois de instalar, abra um terminal e digite:
```bash
ollama pull llama3.2
```
Isso vai baixar o modelo de IA (pode demorar alguns minutos, são vários GB).

### Verificar se funcionou:
```bash
ollama list
```
Se aparecer `llama3.2` na lista, está funcionando! ✅

### Manter o Ollama rodando:
O Ollama precisa estar rodando enquanto você usa o FinGuia. Deixe a janela do terminal aberta ou inicie ele sempre que for usar:
```bash
ollama serve
```

---

## PASSO 5: PREPARAR O PROJETO

### 5.1. Abrir o Terminal na Pasta do Projeto

1. **Windows:**
   - Abra o Explorador de Arquivos
   - Navegue até a pasta `K:\Projetos\FINDGUIA`
   - Clique com botão direito na pasta
   - Selecione "Abrir no Terminal" ou "Abrir no PowerShell"

2. **Mac/Linux:**
   ```bash
   cd /caminho/para/FINDGUIA
   ```

### 5.2. Criar Arquivo de Configuração

1. Na pasta do projeto, procure o arquivo `.env.example`
2. Copie ele e renomeie para `.env`
   - **Windows:** Clique direito > Copiar > Colar > Renomear para `.env`
   - **Mac/Linux:** 
     ```bash
     cp .env.example .env
     ```

3. Abra o arquivo `.env` com um editor de texto (Bloco de Notas, VS Code, etc.)

4. **IMPORTANTE:** Altere a linha `SECRET_KEY` para uma chave aleatória.

**Para que serve a SECRET_KEY?**
A SECRET_KEY é usada para:
- **Assinar os tokens JWT** (os "tickets" de autenticação que você recebe ao fazer login)
- **Garantir segurança** - sem ela, qualquer pessoa poderia criar tokens falsos e acessar contas de outros usuários
- **Criptografar dados sensíveis** quando necessário

**Por que precisa ser aleatória?**
Se alguém descobrir sua SECRET_KEY, pode criar tokens falsos e acessar qualquer conta. Por isso, ela deve ser:
- Longa (pelo menos 32 caracteres)
- Aleatória (não use palavras ou datas)
- Única (cada instalação deve ter uma diferente)

**Como gerar uma chave segura?**

Opção 1 - Usar gerador online:
- Acesse: https://randomkeygen.com/
- Use qualquer uma das chaves da seção "CodeIgniter Encryption Keys" (são longas e aleatórias)
- Copie e cole no arquivo `.env`

Opção 2 - Gerar no terminal (Linux/Mac):
```bash
openssl rand -hex 32
```

Opção 3 - Gerar no Python:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Exemplo de como deve ficar no `.env`:
```
SECRET_KEY=K8j3mN9pQ2rT5vX8zA1bC4eF7hJ0kL3mN6pQ9sT2vW5yZ8aB1cD4eF7hJ0kL
```

**⚠️ ATENÇÃO:** Nunca compartilhe sua SECRET_KEY ou coloque ela em repositórios públicos!

> 💡 **Quer entender melhor?** Veja a explicação completa em [`docs/SECRET_KEY_EXPLAINED.md`](docs/SECRET_KEY_EXPLAINED.md)

5. Verifique se a linha do Ollama está assim:
```
OLLAMA_BASE_URL=http://localhost:11434
```

6. Salve o arquivo (Ctrl+S ou Cmd+S)

---

## PASSO 6: INICIAR OS SERVIÇOS COM DOCKER

### 6.1. Verificar se o Docker está rodando

Abra o Docker Desktop e verifique se está rodando (ícone verde no canto inferior).

### 6.2. Iniciar todos os serviços

No terminal, na pasta do projeto, digite:

```bash
docker-compose up -d
```

**O que isso faz?**
- Baixa e inicia o PostgreSQL (banco de dados)
- Baixa e inicia o Redis (fila de mensagens)
- Baixa e inicia o MinIO (armazenamento de arquivos)
- Inicia o backend da aplicação
- Inicia os workers (processadores de tarefas)

**Primeira vez:** Pode demorar vários minutos enquanto baixa as imagens.

### 6.3. Verificar se está tudo rodando

```bash
docker ps
```

Você deve ver 6 containers rodando:
- `finguia-postgres`
- `finguia-redis`
- `finguia-minio`
- `finguia-backend`
- `finguia-celery-worker`
- `finguia-celery-beat`

Se algum não estiver rodando, veja os logs:
```bash
docker logs finguia-backend
```

---

## PASSO 7: CRIAR O BANCO DE DADOS

### 7.1. Criar as tabelas no banco

No terminal, digite:

**Windows (PowerShell):**
```powershell
Get-Content backend/app/db/schema.sql | docker exec -i finguia-postgres psql -U finguia -d finguia_db
```

**Mac/Linux (Bash):**
```bash
docker exec -i finguia-postgres psql -U finguia -d finguia_db < backend/app/db/schema.sql
```

**Alternativa (funciona em ambos):**
```bash
docker exec -i finguia-postgres psql -U finguia -d finguia_db -f /dev/stdin < backend/app/db/schema.sql
```

Ou copie e cole o conteúdo do arquivo diretamente:
```bash
docker exec -it finguia-postgres psql -U finguia -d finguia_db
```
Depois cole o conteúdo de `backend/app/db/schema.sql` e pressione Enter.

**O que isso faz?**
Cria todas as tabelas necessárias no banco de dados (usuários, boletos, pagamentos, etc.)

### 7.2. Verificar se funcionou

**Windows (PowerShell):**
```powershell
docker exec finguia-postgres psql -U finguia -d finguia_db -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"
```

**Mac/Linux:**
```bash
docker exec -it finguia-postgres psql -U finguia -d finguia_db -c "\dt"
```

**Ou use o script (mais fácil):**
```powershell
.\scripts\verificar_banco.ps1
```

**Para conectar interativamente (modo interativo):**
```powershell
docker exec -it finguia-postgres psql -U finguia -d finguia_db
```
Depois digite `\dt` e pressione Enter. Para sair, digite `\q`.

**⚠️ Nota:** No PowerShell, `-it` pode abrir nova janela. Se isso acontecer, use o comando sem `-it` ou o script.

Deve mostrar uma lista de tabelas (users, accounts, bills, payments, etc.).

---

## PASSO 8: POPULAR COM DADOS DE TESTE

### 8.1. Executar o script de seed via Docker (RECOMENDADO)

**Esta é a forma mais fácil e não requer instalar dependências localmente:**

**Opção 1: Usar o script (MAIS FÁCIL):**

**⚠️ IMPORTANTE:** Execute na pasta raiz do projeto (não dentro de `backend/`):

```powershell
# Certifique-se de estar na pasta raiz (K:\Projetos\FINDGUIA)
cd K:\Projetos\FINDGUIA

# Execute o script
.\scripts\seed_via_docker.ps1
```

**Opção 2: Comando manual (RECOMENDADO se script não funcionar):**

**Certifique-se de estar na pasta raiz do projeto:**
```powershell
cd K:\Projetos\FINDGUIA

# Copiar o script para o container
docker cp scripts/seed_data.py finguia-backend:/app/seed_data.py

# Executar o script
docker exec finguia-backend python /app/seed_data.py
```

**Se der erro de política de execução no script:**
```powershell
# Execute os comandos acima manualmente, ou
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Depois tente o script novamente
```

**Opção 3: Se o container ainda não estiver rodando:**
```powershell
docker-compose run --rm backend bash -c "python -c 'import sys; sys.path.append(\"/app\"); exec(open(\"/app/seed_data.py\").read())'"
```

### 8.2. Alternativa: Instalar localmente (se necessário)

**⚠️ ATENÇÃO:** Se você tem Python 3.13, pode ter problemas com algumas dependências. Recomendamos usar Docker.

Se ainda quiser instalar localmente:

**Windows:**
```powershell
cd backend
python -m pip install --upgrade pip
# Tente instalar com versão mais recente do psycopg2
pip install psycopg2-binary --upgrade
pip install -r requirements.txt
```

**Se der erro com psycopg2-binary:**
- Use Python 3.11 ou 3.12 (mais compatível)
- Ou atualize o requirements.txt para usar versões mais recentes

**O que isso faz?**
Cria um usuário de teste e alguns boletos de exemplo.

**Credenciais criadas:**
- Email: `teste@finguia.com`
- Senha: `senha123`

**💡 DICA:** Se você tiver problemas instalando dependências localmente (especialmente com Python 3.13), use Docker! É mais fácil e não requer instalar nada no seu computador.

### 8.3. Verificar se funcionou

Você deve ver mensagens como:
```
Creating test user...
Created user: teste@finguia.com
Creating test bills...
Created 20 bills
```

---

## PASSO 9: CONFIGURAR O FRONTEND

### 9.1. Ir para a pasta do frontend

**⚠️ IMPORTANTE:** Certifique-se de estar na pasta raiz do projeto primeiro!

```powershell
# Se você estiver na pasta backend, volte para a raiz:
cd K:\Projetos\FINDGUIA

# Agora vá para a pasta frontend:
cd frontend
# ou
cd .\frontend
```

**Mac/Linux:**
```bash
cd frontend
```

### 9.2. Instalar as dependências

**Certifique-se de estar na pasta frontend:**
```powershell
# Se não estiver na pasta frontend:
cd K:\Projetos\FINDGUIA\frontend

# Instalar dependências:
npm install
```

**O que isso faz?**
Baixa todas as bibliotecas necessárias para o frontend (React, TypeScript, Tailwind, etc.)

**Primeira vez:** Pode demorar alguns minutos (2-5 minutos dependendo da conexão).

**⚠️ Se der erro:** Verifique se o Node.js está instalado:
```powershell
node --version  # Deve mostrar v18 ou superior
npm --version   # Deve mostrar versão do npm
```

### 9.3. Iniciar o servidor de desenvolvimento

**Certifique-se de estar na pasta frontend:**
```powershell
# Se não estiver na pasta frontend:
cd K:\Projetos\FINDGUIA\frontend

# Iniciar o servidor:
npm run dev
```

**O que isso faz?**
Inicia o servidor do frontend na porta 3000 usando Vite.

Você deve ver algo como:
```
  VITE v5.0.0  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

**⚠️ IMPORTANTE:** Mantenha este terminal aberto! O frontend precisa estar rodando para você acessar no navegador.

**Para parar o servidor:** Pressione `Ctrl + C` no terminal.

---

## PASSO 10: ACESSAR A APLICAÇÃO

### 10.1. Abrir no navegador

1. Abra seu navegador (Chrome, Firefox, Edge, etc.)
2. Acesse: **http://localhost:3000**

### 10.2. Fazer login

Use as credenciais criadas no Passo 8:
- **Email:** `teste@finguia.com`
- **Senha:** `senha123`

### 10.3. Explorar a aplicação

- **Dashboard:** Veja estatísticas dos seus boletos
- **Boletos:** Veja a lista de boletos cadastrados
- **Upload:** Faça upload de um novo boleto (PDF ou imagem)
- **Pagamentos:** Veja os pagamentos agendados

---

## PASSO 11: TESTAR O UPLOAD DE UM BOLETO

### 11.1. Preparar um arquivo

Tenha um boleto em PDF ou imagem (PNG, JPG) pronto.

### 11.2. Fazer upload

1. No navegador, clique em "Upload" no menu
2. Arraste o arquivo para a área indicada OU clique para selecionar
3. Clique em "Enviar Boleto"

### 11.3. Aguardar processamento

- O sistema vai fazer OCR (extrair texto da imagem)
- Depois vai usar o Ollama para extrair os dados
- Isso pode demorar 30 segundos a 2 minutos

### 11.4. Confirmar os dados

1. Quando o processamento terminar, você verá os dados extraídos
2. Se a confiança for menor que 90%, você precisará confirmar manualmente
3. Revise os campos (emissor, valor, data de vencimento)
4. Clique em "Confirmar" se estiver correto

### 11.5. Agendar pagamento (opcional)

1. Depois de confirmar, você pode agendar o pagamento
2. Escolha a data
3. Escolha o método (PIX, Boleto, etc.)
4. Configure os lembretes (7, 3 e 1 dia antes)

---

## 🐛 RESOLVENDO PROBLEMAS COMUNS

### Problema: Docker não inicia

**Solução:**
- Verifique se o Docker Desktop está rodando
- Reinicie o Docker Desktop
- No Windows, verifique se a virtualização está habilitada no BIOS

### Problema: "Port already in use"

**Solução:**
Algum programa está usando a porta. Pare os serviços:
```bash
docker-compose down
```
E tente novamente.

### Problema: Ollama não responde

**Solução:**
1. Verifique se o Ollama está rodando:
   ```bash
   ollama list
   ```
2. Se não estiver, inicie:
   ```bash
   ollama serve
   ```
3. Se estiver usando Docker, configure no `.env`:
   ```
   OLLAMA_BASE_URL=http://host.docker.internal:11434
   ```

### Problema: "bind: Normalmente é permitida apenas uma utilização de cada endereço de soquete (protocolo/endereço de rede/porta)" - Porta 11434 já em uso

**O que significa?**
O Ollama já está rodando em outro terminal ou processo. Você não precisa iniciar novamente!

**Solução 1: Verificar se já está rodando (RECOMENDADO)**
1. Abra um novo terminal
2. Digite:
   ```bash
   ollama list
   ```
3. Se funcionar (mostrar a lista de modelos), o Ollama JÁ ESTÁ RODANDO! ✅
4. Você pode continuar usando normalmente - não precisa fazer nada mais

**Solução 2: Se realmente precisar reiniciar**

**Windows:**
1. Abra o Gerenciador de Tarefas (Ctrl+Shift+Esc)
2. Vá na aba "Processos" ou "Detalhes"
3. Procure por "ollama" ou "ollama.exe"
4. Clique com botão direito > "Finalizar tarefa"
5. Depois inicie novamente:
   ```bash
   ollama serve
   ```

**Mac/Linux:**
1. Encontre o processo:
   ```bash
   lsof -i :11434
   # ou
   ps aux | grep ollama
   ```
2. Pare o processo:
   ```bash
   kill <PID>
   # ou se não funcionar:
   kill -9 <PID>
   ```
   (Substitua `<PID>` pelo número que apareceu no comando anterior)
3. Depois inicie novamente:
   ```bash
   ollama serve
   ```

**Solução 3: Usar outra porta (avançado)**
Se você realmente precisa rodar duas instâncias do Ollama:
1. Configure uma porta diferente:
   ```bash
   OLLAMA_HOST=127.0.0.1:11435 ollama serve
   ```
2. Atualize o `.env`:
   ```
   OLLAMA_BASE_URL=http://localhost:11435
   ```

**💡 DICA:** Na maioria dos casos, o Ollama já está rodando e você só precisa verificar com `ollama list`. Não precisa iniciar novamente!

**🛠️ Scripts de Verificação Automática:**
- **Windows:** Execute `scripts\verificar_ollama.bat` (clique duplo)
- **Mac/Linux:** Execute `bash scripts/verificar_ollama.sh`

Esses scripts verificam automaticamente se o Ollama está rodando e ajudam a resolver problemas.

### Problema: Erro "bind: porta já em uso" ao iniciar Ollama

**Solução Rápida:**
1. Abra um novo terminal
2. Digite: `ollama list`
3. Se funcionar, o Ollama JÁ ESTÁ RODANDO! ✅ Não precisa fazer nada.

**Se realmente precisar reiniciar:**
- **Windows:** Use o Gerenciador de Tarefas (Ctrl+Shift+Esc) para finalizar "ollama.exe"
- **Mac/Linux:** Use `kill <PID>` (encontre o PID com `lsof -i :11434`)

> 📖 **Guia completo:** Veja [`docs/TROUBLESHOOTING_OLLAMA.md`](docs/TROUBLESHOOTING_OLLAMA.md) para mais detalhes

### Problema: Erro ao fazer upload

**Solução:**
1. Verifique se o MinIO está rodando:
   ```bash
   docker ps | grep minio
   ```
2. Verifique os logs:
   ```bash
   docker logs finguia-backend
   ```

### Problema: Frontend não carrega

**Solução:**
1. Verifique se o servidor está rodando (terminal do `npm run dev`)
2. Verifique se a porta 3000 está livre
3. Tente acessar: http://localhost:8000/api/docs (API deve funcionar)

### Problema: "Module not found" no Python

**Solução:**
```bash
cd backend
pip install -r requirements.txt
```

### Problema: "Module not found" no Node

**Solução:**
```bash
cd frontend
npm install
```

---

## 📝 COMANDOS ÚTEIS

### Ver logs do backend
```bash
docker logs finguia-backend -f
```

### Parar todos os serviços
```bash
docker-compose down
```

### Reiniciar todos os serviços
```bash
docker-compose restart
```

### Ver status dos containers
```bash
docker ps
```

### Acessar o banco de dados
```bash
docker exec -it finguia-postgres psql -U finguia -d finguia_db
```

### Limpar tudo e começar do zero
```bash
docker-compose down -v  # Remove volumes também
docker-compose up -d
```

---

## 🎯 PRÓXIMOS PASSOS

Agora que você tem tudo rodando:

1. **Explore a API:**
   - Acesse: http://localhost:8000/api/docs
   - Teste os endpoints diretamente no navegador

2. **Configure notificações:**
   - Edite o `.env` com suas credenciais de email (SMTP)
   - Configure Twilio para SMS (opcional)
   - Configure FCM para push (opcional)

3. **Personalize:**
   - Ajuste as cores no frontend (`tailwind.config.js`)
   - Modifique os templates de email
   - Adicione novos campos se necessário

---

## 📞 PRECISA DE AJUDA?

Se algo não funcionar:

1. **Verifique os logs:**
   ```bash
   docker logs finguia-backend
   docker logs finguia-celery-worker
   ```

2. **Verifique se todos os serviços estão rodando:**
   ```bash
   docker ps
   ```

3. **Reinicie tudo:**
   ```bash
   docker-compose restart
   ```

4. **Consulte a documentação:**
   - `README.md` - Visão geral
   - `SETUP.md` - Configuração avançada
   - `docs/API_EXAMPLES.md` - Exemplos de API

---

## ✅ CHECKLIST FINAL

Antes de considerar que está tudo funcionando, verifique:

- [ ] Docker Desktop está rodando
- [ ] Ollama está rodando e tem o modelo `llama3.2`
- [ ] Todos os containers Docker estão rodando (6 containers)
- [ ] Frontend está acessível em http://localhost:3000
- [ ] API está acessível em http://localhost:8000/api/docs
- [ ] Consegue fazer login com `teste@finguia.com` / `senha123`
- [ ] Consegue fazer upload de um boleto
- [ ] O boleto é processado e mostra os dados extraídos

---

**Parabéns! 🎉 Você configurou o FinGuia com sucesso!**

Agora você pode começar a usar o sistema para organizar suas finanças pessoais.

