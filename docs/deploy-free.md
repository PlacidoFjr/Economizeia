# Deploy free: Vercel + Render + Postgres + Redis + Brevo

## Frontend na Vercel

Configure o projeto apontando para a pasta `frontend`.

Variaveis:

```env
VITE_API_URL=https://SEU-BACKEND.onrender.com/api/v1
```

## Backend no Render

O arquivo `render.yaml` cria o servico `economizeia-api` usando `backend/Dockerfile`.

Variaveis obrigatorias no Render:

```env
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
FRONTEND_URL=https://SEU-FRONTEND.vercel.app
CORS_ORIGINS=["https://SEU-FRONTEND.vercel.app"]
BREVO_API_KEY=...
BREVO_FROM=...
SMTP_FROM=...
```

Variaveis que o `render.yaml` ja define:

```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
CHATBOT_AI_ENABLED=false
CHATBOT_CACHE_ENABLED=true
BILL_UPLOAD_ENABLED=false
MINIO_ENABLED=false
MASK_SENSITIVE_DATA=true
```

`SECRET_KEY` e gerada pelo Render no blueprint. Se criar o servico manualmente, gere uma chave forte com 32+ caracteres.

## Servicos free recomendados

- Postgres: Supabase Free ou Neon Free.
- Redis: Upstash Redis.
- Email: Brevo API, nao SMTP, para evitar bloqueio de porta SMTP em hospedagens free.

## Ordem de subida

1. Criar Postgres e copiar a connection string.
2. Criar Redis e copiar a URL.
3. Subir backend no Render com as variaveis.
4. Subir frontend na Vercel com `VITE_API_URL`.
5. Voltar no Render e ajustar `FRONTEND_URL` e `CORS_ORIGINS` com a URL final da Vercel.
6. Testar cadastro, confirmacao de email, login, chat e lancamentos.
