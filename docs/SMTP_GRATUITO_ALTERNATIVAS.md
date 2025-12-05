# 📧 Alternativas Gratuitas de SMTP para Railway

## 🆓 Opções Gratuitas (em ordem de recomendação)

### 1. **Resend** ⭐ (Mais Fácil e Moderno)
- **Site**: https://resend.com
- **Limite Grátis**: 3.000 emails/mês
- **Setup**: Muito fácil (5 minutos)
- **Funciona no Railway**: ✅ Sim

**Como configurar:**
1. Crie conta em https://resend.com (gratuito)
2. Vá em **API Keys** → **Create API Key**
3. Copie a chave gerada
4. No Railway, configure:
   - `SMTP_HOST` = `smtp.resend.com`
   - `SMTP_PORT` = `587`
   - `SMTP_USER` = `resend`
   - `SMTP_PASSWORD` = `sua-api-key-aqui`
   - `SMTP_FROM` = `noreply@seudominio.com` (ou use o domínio que eles fornecem)

### 2. **Brevo (antigo Sendinblue)** ⭐⭐
- **Site**: https://www.brevo.com
- **Limite Grátis**: 300 emails/dia (9.000/mês)
- **Setup**: Fácil
- **Funciona no Railway**: ✅ Sim

**Como configurar:**
1. Crie conta em https://www.brevo.com
2. Vá em **SMTP & API** → **SMTP**
3. Copie as credenciais SMTP
4. No Railway, configure:
   - `SMTP_HOST` = `smtp-relay.brevo.com`
   - `SMTP_PORT` = `587`
   - `SMTP_USER` = `seu-email@exemplo.com`
   - `SMTP_PASSWORD` = `sua-smtp-key`
   - `SMTP_FROM` = `seu-email@exemplo.com`

### 3. **Mailgun** ⭐
- **Site**: https://www.mailgun.com
- **Limite Grátis**: 5.000 emails/mês (primeiros 3 meses), depois 1.000/mês
- **Setup**: Médio
- **Funciona no Railway**: ✅ Sim

**Como configurar:**
1. Crie conta em https://www.mailgun.com
2. Vá em **Sending** → **Domain Settings**
3. Use o domínio sandbox ou configure seu domínio
4. Vá em **Sending** → **SMTP Credentials**
5. No Railway, configure:
   - `SMTP_HOST` = `smtp.mailgun.org`
   - `SMTP_PORT` = `587`
   - `SMTP_USER` = `postmaster@seudominio.mailgun.org`
   - `SMTP_PASSWORD` = `sua-smtp-password`
   - `SMTP_FROM` = `noreply@seudominio.com`

### 4. **Zoho Mail** (Gratuito)
- **Site**: https://www.zoho.com/mail
- **Limite Grátis**: 250 emails/dia
- **Setup**: Médio
- **Funciona no Railway**: ✅ Sim

**Como configurar:**
1. Crie conta em https://www.zoho.com/mail
2. Vá em **Settings** → **Mail Accounts** → **POP/IMAP Access**
3. Ative **SMTP Access**
4. Gere **App Password**
5. No Railway, configure:
   - `SMTP_HOST` = `smtp.zoho.com`
   - `SMTP_PORT` = `587`
   - `SMTP_USER` = `seu-email@zoho.com`
   - `SMTP_PASSWORD` = `app-password-gerada`
   - `SMTP_FROM` = `seu-email@zoho.com`

### 5. **Gmail com App Password** (Se Railway Permitir)
- **Limite**: 500 emails/dia
- **Setup**: Fácil
- **Funciona no Railway**: ⚠️ Pode ter problemas de rede

**Como configurar:**
1. Ative 2FA no Gmail
2. Gere App Password: https://myaccount.google.com/apppasswords
3. No Railway, configure:
   - `SMTP_HOST` = `smtp.gmail.com`
   - `SMTP_PORT` = `587` (ou `465` para SSL)
   - `SMTP_USER` = `seu-email@gmail.com`
   - `SMTP_PASSWORD` = `app-password-16-caracteres`
   - `SMTP_FROM` = `seu-email@gmail.com`

## 🏆 Recomendação: **Resend**

**Por quê?**
- ✅ Mais fácil de configurar
- ✅ Interface moderna
- ✅ 3.000 emails/mês grátis
- ✅ Funciona perfeitamente no Railway
- ✅ Documentação excelente
- ✅ Sem verificação de domínio inicial (usa domínio deles)

## 📋 Passo a Passo Rápido - Resend

### 1. Criar Conta (2 minutos)
1. Acesse: https://resend.com
2. Clique em **Sign Up** (pode usar Google/GitHub)
3. Confirme seu email

### 2. Gerar API Key (1 minuto)
1. No dashboard, vá em **API Keys**
2. Clique em **Create API Key**
3. Dê um nome: `EconomizeIA`
4. Copie a chave gerada (começa com `re_...`)

### 3. Configurar no Railway (2 minutos)
1. Railway Dashboard → Seu projeto → **Variables**
2. Adicione/Edite:
   - `SMTP_HOST` = `smtp.resend.com`
   - `SMTP_PORT` = `587`
   - `SMTP_USER` = `resend`
   - `SMTP_PASSWORD` = `re_sua-chave-aqui` (cole a chave que você copiou)
   - `SMTP_FROM` = `onboarding@resend.dev` (temporário, depois você pode usar seu domínio)

### 4. Testar
1. Faça redeploy no Railway
2. Tente criar uma conta
3. Verifique os logs do Railway
4. Verifique sua caixa de entrada (ou spam)

## 🔍 Verificar se Funcionou

Nos logs do Railway, procure por:
- `✅ Email sent successfully to ...` = Funcionou! 🎉
- `❌ SMTP Network Error` = Problema de rede
- `❌ SMTP Authentication failed` = Credenciais erradas

## 💡 Dica

Se você quiser usar seu próprio domínio no Resend (opcional):
1. Vá em **Domains** no Resend
2. Adicione seu domínio
3. Configure os registros DNS
4. Depois use: `SMTP_FROM` = `noreply@seudominio.com`

Mas para começar, pode usar o domínio deles (`onboarding@resend.dev`).

