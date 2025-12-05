# 🔧 Erro de Rede SMTP no Railway

## ❌ Problema Identificado

Nos logs aparece:
```
ERROR: [Errno 101] Network is unreachable
```

Isso significa que o Railway **não consegue conectar** ao servidor SMTP do Gmail.

## 🔍 Possíveis Causas

### 1. Restrições de Rede do Railway
O Railway pode ter restrições de firewall que bloqueiam conexões SMTP externas na porta 587.

### 2. Porta Bloqueada
A porta 587 (SMTP) pode estar bloqueada no Railway.

### 3. Configuração Incorreta
As credenciais SMTP podem estar incorretas ou o servidor SMTP pode não estar acessível.

## ✅ Soluções

### Solução 1: Usar SendGrid (Recomendado para Railway)

SendGrid é otimizado para serviços cloud e funciona melhor no Railway:

1. **Crie conta no SendGrid**: https://sendgrid.com
2. **Gere API Key**:
   - SendGrid Dashboard → **Settings** → **API Keys**
   - **Create API Key**
   - Dê um nome (ex: "EconomizeIA")
   - Permissões: **Full Access** ou **Mail Send**
   - Copie a chave gerada

3. **Configure no Railway**:
   - Railway Dashboard → **Variables**
   - Adicione:
     - `SMTP_HOST` = `smtp.sendgrid.net`
     - `SMTP_PORT` = `587`
     - `SMTP_USER` = `apikey`
     - `SMTP_PASSWORD` = `sua-api-key-do-sendgrid` (a chave que você copiou)
     - `SMTP_FROM` = `noreply@economizeia.com` (ou seu domínio verificado)

4. **Redeploy**

### Solução 2: Usar Resend (Alternativa Moderna)

Resend é uma alternativa moderna e fácil:

1. **Crie conta no Resend**: https://resend.com
2. **Gere API Key**
3. **Configure no Railway**:
   - `SMTP_HOST` = `smtp.resend.com`
   - `SMTP_PORT` = `587`
   - `SMTP_USER` = `resend`
   - `SMTP_PASSWORD` = `sua-api-key-do-resend`
   - `SMTP_FROM` = `noreply@seudominio.com`

### Solução 3: Usar Gmail com App Password (Se Railway Permitir)

Se o Railway permitir conexões SMTP externas:

1. **Crie Senha de App do Gmail**:
   - https://myaccount.google.com/apppasswords
   - Gere senha de app

2. **Configure no Railway**:
   - `SMTP_HOST` = `smtp.gmail.com`
   - `SMTP_PORT` = `587`
   - `SMTP_USER` = `seu-email@gmail.com`
   - `SMTP_PASSWORD` = `senha-de-app-gerada` (16 caracteres)
   - `SMTP_FROM` = `seu-email@gmail.com`

### Solução 4: Usar AWS SES (Para Produção)

AWS SES é robusto e confiável:

1. **Configure AWS SES**
2. **Configure no Railway**:
   - `SMTP_HOST` = `email-smtp.regiao.amazonaws.com` (ex: `email-smtp.us-east-1.amazonaws.com`)
   - `SMTP_PORT` = `587`
   - `SMTP_USER` = `sua-access-key`
   - `SMTP_PASSWORD` = `sua-secret-key`

## 🔍 Verificar se Funcionou

Após configurar, verifique os logs do Railway:

1. Railway Dashboard → **Deploy Logs**
2. Procure por:
   - `✅ Email sent successfully to ...` = Funcionou!
   - `❌ SMTP Network Error` = Ainda com problema de rede
   - `❌ SMTP Authentication failed` = Credenciais erradas

## ⚠️ Importante

**O sistema continua funcionando mesmo se o email falhar!**

- Registro de usuário funciona mesmo sem email
- Login funciona (mas requer verificação de email)
- Você pode verificar emails manualmente no banco se necessário

## 📋 Checklist

- [ ] Escolhi um serviço SMTP (SendGrid, Resend, AWS SES, etc.)
- [ ] Configurei todas as variáveis SMTP no Railway
- [ ] Testei enviar um email
- [ ] Verifiquei os logs do Railway
- [ ] Email chegou na caixa de entrada (ou spam)

## 💡 Dica

Para desenvolvimento/testes, você pode:
1. **Verificar emails manualmente no banco** (marcar `email_verified = true`)
2. **Usar Mailtrap** para capturar emails em desenvolvimento
3. **Temporariamente desabilitar verificação** (não recomendado para produção)

