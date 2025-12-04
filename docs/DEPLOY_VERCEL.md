# 🚀 Deploy no Vercel - EconomizeIA

Guia completo para fazer deploy do frontend no Vercel e backend em serviços compatíveis.

## 📋 Estrutura do Deploy

- **Frontend (React)**: Vercel ✅
- **Backend (FastAPI)**: Railway, Render, ou Fly.io
- **Banco de Dados**: Supabase, Railway PostgreSQL, ou Neon
- **Redis**: Upstash (gratuito)
- **Storage**: Cloudinary ou AWS S3

## 🎯 Opção 1: Frontend no Vercel + Backend no Railway (Recomendado)

### Frontend no Vercel

#### 1. Preparar o Projeto

```bash
cd frontend
```

#### 2. Criar `vercel.json`

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://seu-backend.railway.app/api/$1"
    }
  ],
  "env": {
    "VITE_API_URL": "https://seu-backend.railway.app"
  }
}
```

#### 3. Atualizar `.env` para Produção

Crie `.env.production`:

```env
VITE_API_URL=https://seu-backend.railway.app
```

#### 4. Deploy no Vercel

**Opção A: Via CLI**

```bash
# Instalar Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel

# Deploy em produção
vercel --prod
```

**Opção B: Via GitHub (Recomendado)**

1. Faça push do código para GitHub
2. Acesse [vercel.com](https://vercel.com)
3. Clique em "Add New Project"
4. Importe seu repositório
5. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
6. Adicione variáveis de ambiente:
   - `VITE_API_URL`: URL do seu backend
7. Clique em "Deploy"

### Backend no Railway

#### 1. Criar `railway.json`

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "backend/Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### 2. Criar `Procfile` (alternativa)

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: celery -A app.celery_app worker --loglevel=info
beat: celery -A app.celery_app beat --loglevel=info
```

#### 3. Atualizar `backend/Dockerfile` para Produção

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway usa variável PORT)
EXPOSE $PORT

# Run application
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

#### 4. Deploy no Railway

1. Acesse [railway.app](https://railway.app)
2. Clique em "New Project"
3. Selecione "Deploy from GitHub repo"
4. Escolha seu repositório
5. Railway detecta automaticamente e faz deploy
6. Configure variáveis de ambiente:
   - `DATABASE_URL`: Adicione serviço PostgreSQL
   - `REDIS_URL`: Adicione serviço Redis
   - `SECRET_KEY`: Gere uma chave forte
   - `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`
   - `FRONTEND_URL`: URL do Vercel
   - `CORS_ORIGINS`: `["https://seu-app.vercel.app"]`

#### 5. Adicionar Serviços no Railway

- **PostgreSQL**: Adicione como serviço separado
- **Redis**: Adicione como serviço separado
- **Worker (Celery)**: Adicione novo serviço com comando `celery -A app.celery_app worker`
- **Beat (Celery)**: Adicione novo serviço com comando `celery -A app.celery_app beat`

## 🎯 Opção 2: Tudo no Vercel (Frontend + Serverless Functions)

### Limitações
- Vercel não suporta processos longos (Celery)
- Precisa adaptar para serverless
- Redis pode usar Upstash

### Adaptar Backend para Serverless

Crie `api/` na raiz do projeto:

```
api/
  auth/
    login.py
    register.py
  bills/
    list.py
    create.py
  ...
```

Exemplo `api/bills/list.py`:

```python
from http.server import BaseHTTPRequestHandler
import json
from app.api.v1.bills import list_bills

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Adaptar lógica do FastAPI para serverless
        response = list_bills()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
```

## 🎯 Opção 3: Frontend Vercel + Backend Render

### Backend no Render

1. Acesse [render.com](https://render.com)
2. Clique em "New +" > "Web Service"
3. Conecte seu repositório GitHub
4. Configure:
   - **Name**: economizeia-backend
   - **Environment**: Docker
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Adicione variáveis de ambiente
6. Adicione serviços:
   - PostgreSQL (gratuito)
   - Redis (gratuito)

## 🔧 Configurações Necessárias

### Atualizar CORS no Backend

```python
# backend/app/core/config.py
CORS_ORIGINS: List[str] = [
    "https://seu-app.vercel.app",
    "https://www.seu-app.vercel.app"
]
```

### Atualizar Frontend

```typescript
// frontend/src/lib/api.ts
const API_URL = import.meta.env.VITE_API_URL || 'https://seu-backend.railway.app';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

## 📝 Checklist de Deploy

### Frontend (Vercel)
- [ ] Código no GitHub
- [ ] `vercel.json` configurado
- [ ] Variável `VITE_API_URL` configurada
- [ ] Build funcionando localmente
- [ ] Deploy realizado

### Backend (Railway/Render)
- [ ] Dockerfile configurado
- [ ] Variáveis de ambiente configuradas
- [ ] PostgreSQL adicionado
- [ ] Redis adicionado
- [ ] Celery Worker configurado
- [ ] Celery Beat configurado
- [ ] CORS configurado para domínio Vercel

## 🚀 Deploy Rápido (5 minutos)

### 1. Frontend no Vercel

```bash
cd frontend
npm i -g vercel
vercel login
vercel --prod
```

### 2. Backend no Railway

1. Acesse railway.app
2. New Project > GitHub
3. Selecione repositório
4. Adicione PostgreSQL e Redis
5. Configure variáveis
6. Deploy automático!

## 🔗 URLs de Exemplo

- **Frontend**: `https://economizeia.vercel.app`
- **Backend**: `https://economizeia-backend.railway.app`
- **API Docs**: `https://economizeia-backend.railway.app/api/docs`

## 💰 Custos

### Vercel
- **Gratuito**: Ilimitado para projetos pessoais
- **Pro**: $20/mês (equipes)

### Railway
- **Gratuito**: $5 crédito/mês
- **Pro**: $20/mês

### Render
- **Gratuito**: Tier gratuito disponível
- **Starter**: $7/mês

## 🆘 Troubleshooting

### Frontend não conecta com backend
- Verifique `VITE_API_URL` no Vercel
- Verifique CORS no backend
- Verifique se backend está online

### Erro 404 no Vercel
- Verifique `vercel.json`
- Verifique se `dist/` está sendo gerado
- Verifique build logs no Vercel

### Backend não inicia
- Verifique logs no Railway/Render
- Verifique variáveis de ambiente
- Verifique se `PORT` está configurado

## 📚 Recursos

- [Vercel Documentation](https://vercel.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [Render Documentation](https://render.com/docs)

