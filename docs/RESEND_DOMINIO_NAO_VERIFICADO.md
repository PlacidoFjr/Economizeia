# 🔧 Resolver: Domínio Não Verificado no Resend

## ❌ Problema

Você está vendo este erro nos logs:
```
ResendError: You can only send testing emails to your own email address (leadspark34@gmail.com). 
To send emails to other recipients, please verify a domain at resend.com/domains
```

## ✅ Solução Automática (Já Implementada)

O sistema agora **automaticamente tenta SMTP** quando o Resend falha por domínio não verificado!

### Como Funciona:

1. **Tenta Resend primeiro** (se `RESEND_API_KEY` estiver configurado)
2. **Se falhar por domínio não verificado** → Tenta SMTP automaticamente
3. **Se SMTP também não estiver configurado** → Loga o erro

## 🎯 Opções para Resolver Definitivamente

### Opção 1: Verificar Domínio no Resend (Recomendado) ⭐

**Vantagens:**
- ✅ Envia para qualquer email
- ✅ Mais confiável que SMTP
- ✅ Melhor deliverability
- ✅ Grátis até 3.000 emails/mês

**Passo a Passo:**

1. Acesse: https://resend.com/domains
2. Clique em **"Add Domain"**
3. Digite seu domínio (ex: `economizeia.com`)
4. Configure os registros DNS conforme instruções:
   - **SPF**: `v=spf1 include:_spf.resend.com ~all`
   - **DKIM**: Chave fornecida pelo Resend
   - **DMARC**: `v=DMARC1; p=none;`
5. Aguarde verificação (pode levar algumas horas)
6. No Railway, atualize:
   - `RESEND_FROM` = `noreply@seudominio.com`

### Opção 2: Usar SMTP (Temporário)

**Vantagens:**
- ✅ Funciona imediatamente
- ✅ Não precisa verificar domínio

**Desvantagens:**
- ⚠️ Pode ter problemas de rede no Railway
- ⚠️ Menos confiável que Resend

**Configuração no Railway:**

1. Configure as variáveis SMTP:
   - `SMTP_HOST` = `smtp.gmail.com` (ou outro)
   - `SMTP_PORT` = `587`
   - `SMTP_USER` = seu email
   - `SMTP_PASSWORD` = senha de app do Gmail
   - `SMTP_FROM` = seu email

2. **Remova ou deixe vazio** `RESEND_API_KEY` para usar apenas SMTP

### Opção 3: Usar Ambos (Híbrido) ⭐⭐

**Melhor dos dois mundos:**

1. **Configure Resend** (para quando o domínio estiver verificado)
2. **Configure SMTP** (como fallback)
3. O sistema usa Resend primeiro, e se falhar, usa SMTP automaticamente!

**Configuração no Railway:**

```
RESEND_API_KEY=re_UKsnW6P2_LmdaKNuv4ZTak7hRZquAbhFy
RESEND_FROM=onboarding@resend.dev
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seuemail@gmail.com
SMTP_PASSWORD=senha_de_app
SMTP_FROM=seuemail@gmail.com
```

## 🔍 Como Verificar se Está Funcionando

### Nos Logs do Railway:

**Cenário 1: Resend funcionando**
```
INFO: 📧 Sending email via Resend API to email@exemplo.com
INFO: ✅ Email sent successfully via Resend to email@exemplo.com (ID: abc123)
```

**Cenário 2: Resend falhou, usando SMTP**
```
INFO: 📧 Sending email via Resend API to email@exemplo.com
WARNING: ⚠️ Resend: domínio não verificado ou conta de teste limitada
INFO: ⚠️ Resend falhou, tentando SMTP como fallback para email@exemplo.com
INFO: 📧 Preparing email to email@exemplo.com via SMTP smtp.gmail.com:587
INFO: ✅ Email sent successfully via SMTP to email@exemplo.com
```

## 📝 Notas Importantes

1. **Conta de Teste do Resend:**
   - Só envia para o email cadastrado na conta
   - Para enviar para qualquer email, precisa verificar domínio

2. **SMTP no Railway:**
   - Pode ter problemas de firewall/rede
   - Use senha de app do Gmail (não a senha normal)
   - Gmail: https://myaccount.google.com/apppasswords

3. **Fallback Automático:**
   - O sistema já faz isso automaticamente!
   - Não precisa fazer nada além de configurar SMTP

## ✅ Próximos Passos

1. **Agora mesmo:** Configure SMTP no Railway para funcionar imediatamente
2. **Depois:** Verifique um domínio no Resend para melhorar deliverability
3. **Opcional:** Remova SMTP depois que o domínio estiver verificado

## 🆘 Ainda Não Funciona?

1. Verifique os logs do Railway
2. Confirme que as variáveis estão configuradas corretamente
3. Teste enviando um email para você mesmo primeiro
4. Verifique se o email está na caixa de spam

