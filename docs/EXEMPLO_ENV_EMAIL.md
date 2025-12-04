# 📧 Exemplo de Configuração de Email no .env

## Arquivo `.env` Completo com Email

```env
# Database
DATABASE_URL=postgresql://finguia:finguia_dev@localhost:5432/finguia_db

# Redis
REDIS_URL=redis://localhost:6380/0

# Security
SECRET_KEY=sua-chave-secreta-aqui-mude-em-producao
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# MinIO / S3
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_NAME=finguia-documents
MINIO_USE_SSL=false

# ============================================
# CONFIGURAÇÃO DE EMAIL (SMTP)
# ============================================

# Para Gmail:
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seuemail@gmail.com
SMTP_PASSWORD=sua_senha_de_app_do_gmail
SMTP_FROM=noreply@finguia.com

# Para Outlook:
# SMTP_HOST=smtp-mail.outlook.com
# SMTP_PORT=587
# SMTP_USER=seuemail@outlook.com
# SMTP_PASSWORD=sua_senha
# SMTP_FROM=noreply@finguia.com

# Para SendGrid:
# SMTP_HOST=smtp.sendgrid.net
# SMTP_PORT=587
# SMTP_USER=apikey
# SMTP_PASSWORD=sua_api_key_sendgrid
# SMTP_FROM=noreply@seudominio.com

# Frontend URL (para links nos emails)
FRONTEND_URL=http://localhost:3000

# SMS (Twilio) - Opcional
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# FCM - Opcional
FCM_SERVER_KEY=
FCM_PROJECT_ID=

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# LGPD
DATA_RETENTION_DAYS=365
MASK_SENSITIVE_DATA=true

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

---

## 🔑 Como Obter Senha de App do Gmail

1. Acesse: https://myaccount.google.com/apppasswords
2. Faça login na sua conta Google
3. Selecione "Mail" e "Outro (nome personalizado)"
4. Digite: "FinGuia"
5. Clique em "Gerar"
6. Copie a senha de 16 caracteres gerada
7. Use essa senha no `SMTP_PASSWORD` (não use sua senha normal do Gmail!)

---

## ⚠️ Importante

- **NUNCA** commite o arquivo `.env` no Git (já está no `.gitignore`)
- Use senhas de app para Gmail, não a senha normal
- Em produção, use serviços profissionais (SendGrid, Mailgun, SES)
- Teste sempre antes de colocar em produção

