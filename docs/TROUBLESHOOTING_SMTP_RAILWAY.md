# 🔧 Troubleshooting: SMTP no Railway

## ✅ Suas Configurações Estão Corretas!

```
SMTP_HOST=smtp.gmail.com ✅
SMTP_PORT=587 ✅
SMTP_USER=placidojunior34@gmail.com ✅
SMTP_PASSWORD=qseelwkagwhoqtyt ✅ (senha de app)
SMTP_FROM=noreply@economizeia.com ✅
```

## ❌ Problema: "Network is unreachable"

Este erro acontece quando o **Railway não consegue conectar ao Gmail SMTP**.

### Possíveis Causas:

1. **Firewall do Railway bloqueando porta 587**
   - Alguns provedores de cloud bloqueiam portas SMTP
   - Railway pode ter restrições de rede

2. **Gmail bloqueando IPs do Railway**
   - Gmail pode bloquear conexões de IPs desconhecidos
   - Pode ser temporário

3. **Problema de DNS no Railway**
   - Railway pode não conseguir resolver `smtp.gmail.com`

## 🔍 Como Diagnosticar

### 1. Verificar Logs do Railway

Procure por estas mensagens:

**Sucesso:**
```
INFO: 📧 Preparing email to email@exemplo.com via SMTP smtp.gmail.com:587
INFO: Connecting to SMTP server smtp.gmail.com:587 (timeout=60s)
INFO: Starting TLS...
INFO: Logging in as placidojunior34@gmail.com
INFO: Sending message to email@exemplo.com...
INFO: ✅ Email sent successfully via SMTP to email@exemplo.com
```

**Erro de Rede:**
```
ERROR: ❌ SMTP Network Error: Network is unreachable
```

**Erro de Autenticação:**
```
ERROR: ❌ SMTP Authentication failed
```

### 2. Testar Conexão SMTP

Se possível, teste de outro lugar (não Railway) para confirmar que as credenciais estão corretas.

## 💡 Soluções

### Solução 1: Usar Porta Alternativa (465 com SSL)

Se a porta 587 não funcionar, tente 465 com SSL:

**No Railway, altere:**
```
SMTP_PORT=465
```

**E no código, use `SMTP_SSL` ao invés de `SMTP` + `starttls()`**

Mas isso requer mudança no código. Por enquanto, vamos tentar outras soluções primeiro.

### Solução 2: Verificar Configurações do Gmail

1. **Ativar "Acesso a apps menos seguros"** (não recomendado, mas pode funcionar)
   - https://myaccount.google.com/lesssecureapps
   - ⚠️ Não é mais suportado pelo Google

2. **Usar senha de app** (você já está usando ✅)
   - https://myaccount.google.com/apppasswords

3. **Verificar se a conta não está bloqueada**
   - Tente fazer login no Gmail normalmente
   - Verifique se não há alertas de segurança

### Solução 3: Usar Serviço de Email Dedicado

Se SMTP continuar falhando no Railway, considere:

1. **SendGrid** (gratuito até 100 emails/dia)
2. **Mailgun** (gratuito até 5.000 emails/mês)
3. **Amazon SES** (muito barato)
4. **Resend** (3.000 emails/mês grátis, mas precisa verificar domínio)

### Solução 4: Verificar Rede do Railway

1. **Redeploy** no Railway
   - Às vezes resolve problemas temporários de rede

2. **Verificar região do Railway**
   - Tente mudar a região do deployment
   - Algumas regiões podem ter melhor conectividade

3. **Aguardar alguns minutos**
   - Problemas de rede podem ser temporários
   - Tente novamente depois

## 🔍 Debug Avançado

### Adicionar mais logs:

O código já tem logs detalhados. Verifique:
- Se a conexão está sendo tentada
- Em que ponto falha (conexão, TLS, login, envio)
- Qual é o erro exato

### Testar localmente:

Se funcionar localmente mas não no Railway, confirma que é problema de rede do Railway.

## ✅ Checklist

- [ ] Configurações corretas no Railway
- [ ] Senha de app do Gmail (não senha normal)
- [ ] Verificação em 2 etapas ativada
- [ ] Testou fazer login no Gmail normalmente
- [ ] Verificou logs do Railway
- [ ] Tentou redeploy
- [ ] Aguardou alguns minutos e tentou novamente

## 🚨 Se Nada Funcionar

**Alternativa recomendada:** Use um serviço de email dedicado como SendGrid ou Mailgun, que são mais confiáveis em ambientes cloud como Railway.

**SendGrid (Recomendado):**
- Gratuito até 100 emails/dia
- API simples
- Funciona perfeitamente no Railway
- Setup em 5 minutos

Quer que eu configure SendGrid para você?

