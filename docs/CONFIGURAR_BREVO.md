# 🚀 Configurar Brevo (Sendinblue) API

## ✅ Vantagens

- ✅ **300 emails/dia grátis**
- ✅ **Não precisa de domínio** (pode usar qualquer email verificado)
- ✅ **API REST** (não depende de SMTP, funciona perfeitamente no Railway)
- ✅ **Mais confiável** que SMTP em ambientes cloud
- ✅ **Setup super rápido** (2 minutos)

## 📋 Passo a Passo

### 1. Criar Conta no Brevo

1. Acesse: https://www.brevo.com
2. Clique em **"Sign Up Free"**
3. Preencha seus dados e confirme o email
4. Faça login na sua conta

### 2. Obter API Key

1. No dashboard do Brevo, vá em **Settings** → **SMTP & API**
2. Na seção **"API Keys"**, clique em **"Generate a new API key"**
3. Dê um nome (ex: "EconomizeIA Railway")
4. **Copie a API Key** (ela só aparece uma vez!)

### 3. Verificar Email de Envio

1. No Brevo, vá em **Settings** → **Senders**
2. Clique em **"Add a sender"**
3. Digite seu email (ex: `placidojunior34@gmail.com`)
4. Confirme o email (vai receber um email de verificação)
5. Após verificar, esse email pode ser usado para enviar

### 4. Configurar no Railway

1. **Railway Dashboard** → Seu projeto → **Variables**

2. **Adicione estas variáveis:**
   - `BREVO_API_KEY` = sua API key do Brevo
   - `BREVO_FROM` = seu email verificado (ex: `placidojunior34@gmail.com`)

3. **Você NÃO precisa mais das variáveis SMTP!** (pode remover se quiser)

### 5. Redeploy

Após adicionar as variáveis, o Railway faz redeploy automaticamente.

## 🔍 Verificar se Funcionou

### Nos Logs do Railway:
```
INFO: 📧 Sending email via Brevo API to email@exemplo.com
INFO: ✅ Email sent successfully via Brevo to email@exemplo.com (ID: abc123)
```

### Na Caixa de Entrada:
- Verifique o email (pode estar em spam inicialmente)
- O email deve vir do endereço configurado em `BREVO_FROM`

## ⚙️ Como Funciona

O sistema agora:
1. **Primeiro tenta Brevo API** (se `BREVO_API_KEY` estiver configurado)
2. **Se Brevo falhar**, tenta SMTP como fallback automaticamente
3. **Brevo tem prioridade** - mais confiável!

## 🎯 Variáveis Necessárias no Railway

**Mínimo necessário:**
- ✅ `BREVO_API_KEY` = sua API key do Brevo
- ✅ `BREVO_FROM` = seu email verificado

**Opcional (fallback):**
- `SMTP_HOST` (usado se Brevo falhar)
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `SMTP_FROM`

## 💡 Limites Gratuitos

- **300 emails/dia** (plano gratuito)
- **Sem limite de emails/mês** (desde que não ultrapasse 300/dia)
- Perfeito para começar!

## 🚨 Se Não Funcionar

1. **Verifique se a API Key está correta** no Railway
2. **Verifique se o email está verificado** no Brevo (Settings → Senders)
3. **Verifique os logs** - deve mostrar qual método está sendo usado
4. **Teste a API Key** diretamente no Brevo Dashboard

## ✅ Pronto!

Agora seus emails vão funcionar perfeitamente no Railway! 🎉

