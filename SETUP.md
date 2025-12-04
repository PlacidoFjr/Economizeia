# Guia de Configuração - FinGuia

## Pré-requisitos

- Docker e Docker Compose instalados
- Python 3.11+ (para desenvolvimento local)
- Node.js 18+ (para desenvolvimento local)
- Ollama instalado e rodando

## Instalação do Ollama

### Linux/Mac
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Windows
Baixe o instalador em: https://ollama.ai/download

### Baixar Modelo
```bash
ollama pull llama3.2
# ou
ollama pull mistral
```

## Configuração Inicial

### 1. Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env` e configure:

```bash
cp .env.example .env
```

Edite `.env` com suas configurações:
- `SECRET_KEY`: Gere uma chave secreta forte
- `DATABASE_URL`: URL do PostgreSQL
- `OLLAMA_BASE_URL`: URL do Ollama (padrão: http://localhost:11434)
- `SMTP_*`: Configurações de email (opcional)

### 2. Iniciar Serviços com Docker

```bash
docker-compose up -d
```

Isso iniciará:
- PostgreSQL (porta 5432)
- Redis (porta 6379)
- MinIO (portas 9000 e 9001)
- Backend FastAPI (porta 8000)
- Celery Worker
- Celery Beat

### 3. Criar Banco de Dados

```bash
# Conectar ao PostgreSQL
docker exec -it finguia-postgres psql -U finguia -d finguia_db

# Ou executar o schema SQL
# Windows (PowerShell):
Get-Content backend/app/db/schema.sql | docker exec -i finguia-postgres psql -U finguia -d finguia_db

# Mac/Linux:
docker exec -i finguia-postgres psql -U finguia -d finguia_db < backend/app/db/schema.sql
```

### 4. Popular Dados de Teste

```bash
cd backend
python scripts/seed_data.py
```

Ou via Docker:
```bash
docker exec -it finguia-backend python scripts/seed_data.py
```

## Desenvolvimento Local

### Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Executar migrações (se usar Alembic)
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Iniciar servidor de desenvolvimento
npm run dev
```

### Celery Worker (Backend)

```bash
cd backend
celery -A app.celery_app worker --loglevel=info
```

### Celery Beat (Agendador)

```bash
cd backend
celery -A app.celery_app beat --loglevel=info
```

## Acessos

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **Frontend**: http://localhost:3000
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin123)

## Testes

### Backend

```bash
cd backend
pytest
```

### Frontend

```bash
cd frontend
npm test
```

### Testes de API (curl)

```bash
chmod +x scripts/test_api.sh
./scripts/test_api.sh
```

## Estrutura do Projeto

```
FINDGUIA/
├── backend/              # API FastAPI
│   ├── app/
│   │   ├── api/         # Endpoints
│   │   ├── core/        # Configurações
│   │   ├── db/          # Modelos e database
│   │   ├── services/    # Serviços (OCR, Ollama, etc)
│   │   ├── tasks/       # Tarefas Celery
│   │   └── prompts/     # Templates Ollama
│   ├── tests/           # Testes
│   └── requirements.txt
├── frontend/            # React + TypeScript
│   ├── src/
│   │   ├── components/  # Componentes React
│   │   ├── pages/       # Páginas
│   │   ├── contexts/    # Contextos (Auth)
│   │   └── services/    # Serviços API
│   └── package.json
├── scripts/             # Scripts auxiliares
├── docs/               # Documentação
└── docker-compose.yml  # Orquestração Docker
```

## Troubleshooting

### Ollama não está acessível

Verifique se o Ollama está rodando:
```bash
ollama list
```

Se estiver usando Docker, configure `OLLAMA_BASE_URL=http://host.docker.internal:11434`

### Erro de conexão com banco

Verifique se o PostgreSQL está rodando:
```bash
docker ps | grep postgres
```

### Erro de permissão no MinIO

Verifique as credenciais em `.env` e no `docker-compose.yml`

### Celery não processa tarefas

Verifique se o Redis está rodando:
```bash
docker ps | grep redis
```

Verifique os logs:
```bash
docker logs finguia-celery-worker
```

## Próximos Passos

1. Configure SMTP para notificações por email
2. Configure provider de SMS (Twilio, etc)
3. Configure FCM para push notifications
4. Ajuste as configurações de segurança para produção
5. Configure backup automático do banco de dados

## Suporte

Para problemas ou dúvidas, consulte:
- `README.md` - Visão geral
- `docs/SECURITY.md` - Segurança
- `docs/COMPLIANCE.md` - LGPD
- `docs/API_EXAMPLES.md` - Exemplos de API

