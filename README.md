# FinGuia - Sistema de Organização Financeira Pessoal

Sistema completo para gestão de boletos e faturas com OCR, classificação semântica via Ollama, agendamento de pagamentos e notificações.

## 🏗️ Arquitetura

- **Backend**: FastAPI (Python)
- **Frontend**: React + TypeScript + Tailwind CSS
- **Banco de Dados**: PostgreSQL
- **Fila de Jobs**: Redis + Celery
- **Storage**: MinIO (S3 compatible)
- **AI/ML**: Ollama (local ou cloud)
- **OCR**: Tesseract / OCRmyPDF

## 🚀 Início Rápido

### 📚 Guias Disponíveis

- **👶 Para Iniciantes:** [`GUIA_PASSO_A_PASSO.md`](GUIA_PASSO_A_PASSO.md) - Guia completo e detalhado passo a passo
- **⚡ Para Experientes:** [`QUICK_START.md`](QUICK_START.md) - Setup rápido em 5 minutos
- **🔧 Configuração Avançada:** [`SETUP.md`](SETUP.md) - Detalhes técnicos e troubleshooting

### Pré-requisitos

- Docker e Docker Compose
- Python 3.11+
- Node.js 18+
- Ollama instalado e rodando (ou endpoint configurável)

### Configuração Rápida

1. **Configure o ambiente:**
   ```bash
   cp .env.example .env
   # Edite .env com suas configurações (especialmente SECRET_KEY)
   ```

2. **Inicie os serviços:**
   ```bash
   docker-compose up -d
   ```

3. **Crie o banco de dados:**
   
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

4. **Popule dados de teste:**
   ```bash
   cd backend
   pip install -r requirements.txt
   python scripts/seed_data.py
   ```

5. **Inicie o frontend:**
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```

6. **Acesse:**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/api/docs
   - Login: `teste@finguia.com` / `senha123`

### Configuração do Ollama

O sistema espera que o Ollama esteja rodando. Você pode:

1. **Instalar localmente**: https://ollama.ai
2. **Usar endpoint remoto**: Configure `OLLAMA_BASE_URL` no `.env`

Modelo recomendado: `llama3.2` ou `mistral`

Para baixar o modelo:
```bash
ollama pull llama3.2
ollama serve  # Mantenha rodando em um terminal
```

## 📁 Estrutura do Projeto

```
FINDGUIA/
├── backend/          # API FastAPI
├── frontend/         # React + TypeScript
├── docker/           # Configurações Docker
├── scripts/          # Scripts de seed e testes
└── docs/             # Documentação
```

## 🔐 Segurança

- Autenticação JWT com refresh tokens
- Hashing de senhas com Argon2id
- Criptografia AES-256 para dados sensíveis
- TLS obrigatório em produção
- Logs de auditoria imutáveis
- Compliance LGPD

## 📊 Endpoints Principais

### Autenticação
- `POST /api/v1/auth/register` - Registro de usuário
- `POST /api/v1/auth/login` - Login (retorna JWT)
- `POST /api/v1/auth/refresh` - Refresh token

### Boletos
- `POST /api/v1/bills/upload` - Upload de boleto (PDF/IMG)
- `GET /api/v1/bills/{id}` - Detalhes do boleto
- `POST /api/v1/bills/{id}/confirm` - Confirmar/corrigir dados
- `POST /api/v1/bills/{id}/schedule` - Agendar pagamento
- `POST /api/v1/bills/{id}/mark-paid` - Marcar como pago

### Pagamentos
- `GET /api/v1/payments` - Listar pagamentos
- `POST /api/v1/payments/{id}/reconcile` - Reconciliar com extrato

### Notificações
- `POST /api/v1/notifications/test` - Testar notificação
- `GET /api/v1/notifications/logs` - Logs de notificações

## 🧪 Testes

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## 📝 Licença

Proprietário - Uso interno

