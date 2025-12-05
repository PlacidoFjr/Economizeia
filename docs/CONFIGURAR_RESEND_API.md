# 🚀 Configurar Resend API (Mais Fácil e Confiável)

## ✅ Vantagens da API Resend

- ✅ **Mais confiável** que SMTP (não depende de conexões de rede)
- ✅ **Funciona perfeitamente no Railway** (sem problemas de firewall)
- ✅ **Mais rápido** que SMTP
- ✅ **3.000 emails/mês grátis**
- ✅ **Setup super fácil** (2 minutos)

## 📋 Passo a Passo

### 1. Você já tem a API Key! 🎉

Sua chave: `re_UKsnW6P2_LmdaKNuv4ZTak7hRZquAbhFy`

### 2. Configurar no Railway

1. **Railway Dashboard** → Seu projeto → **Variables**

2. **Adicione estas variáveis:**
   - `RESEND_API_KEY` = `re_UKsnW6P2_LmdaKNuv4ZTak7hRZquAbhFy`
   - `RESEND_FROM` = `onboarding@resend.dev` (ou seu domínio se tiver)

3. **Você NÃO precisa mais das variáveis SMTP!** (pode remover se quiser)

### 3. Redeploy

Após adicionar as variáveis, o Railway faz redeploy automaticamente.

### 4. Testar

1. Tente criar uma conta nova
2. Verifique os logs do Railway
3. Procure por: `📧 Sending email via Resend API`
4. Deve aparecer: `✅ Email sent successfully via Resend`

## 🔍 Verificar se Funcionou

### Nos Logs do Railway:
```
INFO:app.services.notification_service:📧 Sending email via Resend API to email@exemplo.com
INFO:app.services.notification_service:✅ Email sent successfully via Resend to email@exemplo.com (ID: abc123)
```

### Na Caixa de Entrada:
- Verifique o email (pode estar em spam inicialmente)
- O email deve vir de `onboarding@resend.dev`

## ⚙️ Como Funciona

O sistema agora:
1. **Primeiro tenta Resend API** (se `RESEND_API_KEY` estiver configurado)
2. **Se Resend falhar** (ex: domínio não verificado), **automaticamente tenta SMTP**
3. **Se não tiver Resend**, usa SMTP como fallback
4. **Resend tem prioridade** - mais confiável!

## ⚠️ Limitação da Conta de Teste

**Importante:** Com a conta de teste do Resend, você só pode enviar emails para o próprio email cadastrado (`leadspark34@gmail.com`).

**Para enviar para qualquer email:**
- Verifique um domínio em https://resend.com/domains
- Ou configure SMTP como fallback (o sistema faz isso automaticamente!)

**Solução Automática:**
- Se Resend falhar por domínio não verificado, o sistema **automaticamente tenta SMTP**
- Configure SMTP no Railway para ter fallback automático

## 🎯 Variáveis Necessárias no Railway

**Mínimo necessário:**
- ✅ `RESEND_API_KEY` = `re_UKsnW6P2_LmdaKNuv4ZTak7hRZquAbhFy`
- ✅ `RESEND_FROM` = `onboarding@resend.dev`

**Opcional (pode remover se quiser):**
- `SMTP_HOST` (não precisa mais)
- `SMTP_PORT` (não precisa mais)
- `SMTP_USER` (não precisa mais)
- `SMTP_PASSWORD` (não precisa mais)

## 💡 Usar Seu Próprio Domínio (Opcional)

Se quiser usar `noreply@seudominio.com`:

1. Resend Dashboard → **Domains** → **Add Domain**
2. Configure os registros DNS
3. Após verificação, use:
   - `RESEND_FROM` = `noreply@seudominio.com`

Mas para começar, `onboarding@resend.dev` funciona perfeitamente!

## 🚨 Se Não Funcionar

1. **Verifique se a API Key está correta** no Railway
2. **Verifique os logs** - deve mostrar qual método está sendo usado
3. **Teste a API Key** no código Python que você mostrou
4. **Verifique se o email está em spam**

## ✅ Pronto!

Agora seus emails vão funcionar perfeitamente no Railway! 🎉

