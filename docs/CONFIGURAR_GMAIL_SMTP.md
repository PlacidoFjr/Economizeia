# 📧 Configurar Gmail SMTP no Railway

## ✅ Configuração Correta

### Variáveis no Railway:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seuemail@gmail.com
SMTP_PASSWORD=senha_de_app_do_gmail
SMTP_FROM=seuemail@gmail.com
```

## 🔑 Porta 587 (TLS) - CORRETA ✅

A porta **587** é a porta correta para Gmail com TLS (StartTLS). 

**Outras portas do Gmail:**
- **465** = SSL (não usamos)
- **587** = TLS (✅ usamos esta)
- **25** = Não suportado pelo Gmail

## 🔐 Senha de App do Gmail

**IMPORTANTE:** Você NÃO pode usar sua senha normal do Gmail!

### Como criar senha de app:

1. Acesse: https://myaccount.google.com/apppasswords
2. Faça login na sua conta Google
3. Selecione "App" → "Mail"
4. Selecione "Device" → "Other (Custom name)"
5. Digite: "EconomizeIA Railway"
6. Clique em "Generate"
7. **Copie a senha gerada** (16 caracteres, sem espaços)
8. Use essa senha no `SMTP_PASSWORD`

### Se não aparecer "App passwords":

1. Ative a verificação em 2 etapas primeiro:
   - https://myaccount.google.com/security
   - Ative "Verificação em duas etapas"
2. Depois volte para criar a senha de app

## ✅ Verificar se Está Funcionando

### Nos Logs do Railway:

**Sucesso:**
```
INFO: 📧 Preparing email to email@exemplo.com via SMTP smtp.gmail.com:587
INFO: Connecting to SMTP server smtp.gmail.com:587
INFO: Starting TLS...
INFO: Logging in as seuemail@gmail.com
INFO: Sending message to email@exemplo.com...
INFO: ✅ Email sent successfully via SMTP to email@exemplo.com
```

**Erro de Autenticação:**
```
ERROR: ❌ SMTP Authentication failed
```
→ Verifique se está usando **senha de app**, não senha normal!

**Erro de Rede:**
```
ERROR: ❌ SMTP Network Error: Network is unreachable
```
→ Problema de firewall/rede do Railway (pode acontecer, mas é raro)

## 🚨 Problemas Comuns

### 1. "Authentication failed"
- ✅ Use **senha de app**, não senha normal
- ✅ Verifique se a verificação em 2 etapas está ativada

### 2. "Network is unreachable"
- ⚠️ Problema de rede do Railway
- 💡 Considere usar um serviço de email dedicado (SendGrid, Mailgun) se persistir

### 3. "Connection refused"
- ✅ Verifique se `SMTP_HOST` está correto: `smtp.gmail.com`
- ✅ Verifique se `SMTP_PORT` está correto: `587`

## 📝 Checklist

- [ ] `SMTP_HOST` = `smtp.gmail.com`
- [ ] `SMTP_PORT` = `587`
- [ ] `SMTP_USER` = seu email completo (ex: `seuemail@gmail.com`)
- [ ] `SMTP_PASSWORD` = senha de app (16 caracteres)
- [ ] `SMTP_FROM` = mesmo email do `SMTP_USER`
- [ ] Verificação em 2 etapas ativada no Google
- [ ] Senha de app criada corretamente

## ✅ Pronto!

Após configurar, o sistema vai usar Gmail SMTP automaticamente. Teste criando uma conta nova e verifique se o email de verificação chega!

