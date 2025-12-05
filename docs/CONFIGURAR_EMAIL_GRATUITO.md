# 📧 Configurar Email Gratuito (Sem Domínio)

## ✅ Opções Gratuitas

### Opção 1: Outlook/Hotmail SMTP (Recomendado) ⭐

**Vantagens:**
- ✅ Totalmente gratuito
- ✅ Não precisa de domínio
- ✅ Pode funcionar melhor no Railway que Gmail
- ✅ 300 emails/dia grátis

**Configuração no Railway:**

```
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=seuemail@outlook.com (ou @hotmail.com)
SMTP_PASSWORD=senha_do_outlook
SMTP_FROM=seuemail@outlook.com
```

**Como criar conta:**
1. Acesse: https://outlook.com
2. Crie uma conta gratuita
3. Use essa conta para enviar emails

### Opção 2: Brevo (Sendinblue) - API ⭐⭐

**Vantagens:**
- ✅ 300 emails/dia grátis
- ✅ API REST (não precisa SMTP)
- ✅ Funciona perfeitamente no Railway
- ✅ Não precisa de domínio (pode usar email verificado)

**Configuração:**
1. Acesse: https://www.brevo.com
2. Crie conta gratuita
3. Vá em Settings → SMTP & API
4. Crie uma API Key
5. No Railway, adicione:
   ```
   BREVO_API_KEY=sua_api_key_aqui
   BREVO_FROM=seuemail@exemplo.com
   ```

### Opção 3: Zoho Mail SMTP

**Vantagens:**
- ✅ Gratuito
- ✅ SMTP funciona bem

**Configuração:**
```
SMTP_HOST=smtp.zoho.com
SMTP_PORT=587
SMTP_USER=seuemail@zoho.com
SMTP_PASSWORD=senha_do_zoho
SMTP_FROM=seuemail@zoho.com
```

## 🎯 Recomendação

**Para começar rápido:** Use **Outlook SMTP** - só precisa criar uma conta Outlook e configurar no Railway.

**Para mais confiabilidade:** Use **Brevo API** - mais confiável que SMTP em ambientes cloud.

## ⚠️ Limitações

- **Outlook:** 300 emails/dia
- **Brevo:** 300 emails/dia
- **Zoho:** 25 emails/dia (plano gratuito)

Para produção com muitos emails, considere verificar um domínio (gratuito com Freenom ou similar).

