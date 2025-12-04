# ⚡ Quick Start - FinGuia

Guia rápido para quem já tem experiência com Docker e desenvolvimento.

## Pré-requisitos Rápidos

```bash
# Verificar instalações
docker --version
python --version  # 3.11+
node --version    # 18+
ollama --version
```

## Setup em 5 Minutos

### 1. Configurar ambiente
```bash
cp .env.example .env
# Editar .env: SECRET_KEY e OLLAMA_BASE_URL
```

### 2. Iniciar serviços
```bash
docker-compose up -d
```

### 3. Criar banco

**Windows (PowerShell):**
```powershell
Get-Content backend/app/db/schema.sql | docker exec -i finguia-postgres psql -U finguia -d finguia_db
```

**Mac/Linux:**
```bash
docker exec -i finguia-postgres psql -U finguia -d finguia_db < backend/app/db/schema.sql
```

**Ou use o script:**
```powershell
.\scripts\criar_banco.ps1
```

### 4. Popular dados
```bash
cd backend
pip install -r requirements.txt
python scripts/seed_data.py
```

### 5. Iniciar frontend
```bash
cd ../frontend
npm install
npm run dev
```

### 6. Acessar
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/api/docs
- Login: `teste@finguia.com` / `senha123`

## Comandos Úteis

```bash
# Ver logs
docker logs finguia-backend -f

# Parar tudo
docker-compose down

# Reiniciar
docker-compose restart

# Limpar volumes
docker-compose down -v
```

## Troubleshooting

**Ollama não responde:**
```bash
ollama serve  # Em terminal separado
# Ou configurar: OLLAMA_BASE_URL=http://host.docker.internal:11434
```

**Porta ocupada:**
```bash
docker-compose down
# Alterar portas no docker-compose.yml se necessário
```

**Erro de módulo:**
```bash
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
```

---

📖 **Para guia detalhado, veja:** `GUIA_PASSO_A_PASSO.md`

