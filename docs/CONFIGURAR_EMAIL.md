# 📧 Configuração de Envio de Email - FinGuia

## Status Atual

**⚠️ ATENÇÃO: O SMTP NÃO ESTÁ CONFIGURADO**

Atualmente, o sistema de email está **desabilitado**. Quando você solicita redefinição de senha ou outras notificações por email:

- ✅ O sistema gera o token/link corretamente
- ⚠️ O email **NÃO é enviado** (SMTP não configurado)
- 📝 O link aparece nos **logs do backend** para desenvolvimento

---

## Como Funciona o Envio de Email

### 1. **Serviço de Notificação** (`notification_service.py`)

O sistema usa o módulo `smtplib` do Python para enviar emails através de SMTP.

**Fluxo:**
1. Verifica se `SMTP_HOST` está configurado
2. Se não estiver → retorna `False` e loga aviso
3. Se estiver → conecta ao servidor SMTP
4. Autentica com usuário/senha (se necessário)
5. Envia email em formato HTML e texto

### 2. **Onde é Usado**

- ✅ **Redefinição de Senha**: Envia link para redefinir senha
- ✅ **Lembretes de Boletos**: Notifica antes do vencimento
- ✅ **Notificações Gerais**: Outras notificações do sistema

---

## 🔧 Como Configurar o Envio de Email

### Opção 1: Gmail (Recomendado para Testes)

1. **Criar Senha de App no Gmail:**
   - Acesse: https://myaccount.google.com/apppasswords
   - Gere uma senha de app para "Mail"
   - Copie a senha gerada (16 caracteres)

2. **Configurar no `.env`:**
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=seuemail@gmail.com
   SMTP_PASSWORD=senha_de_app_gerada
   SMTP_FROM=noreply@finguia.com
   ```

### Opção 2: Outlook/Hotmail

```env
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=seuemail@outlook.com
SMTP_PASSWORD=sua_senha
SMTP_FROM=noreply@finguia.com
```

### Opção 3: Serviços de Email Profissionais

#### SendGrid
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=sua_api_key_sendgrid
SMTP_FROM=noreply@seudominio.com
```

#### Mailgun
```env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@seudominio.mailgun.org
SMTP_PASSWORD=sua_senha_mailgun
SMTP_FROM=noreply@seudominio.com
```

#### Amazon SES
```env
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=sua_access_key
SMTP_PASSWORD=sua_secret_key
SMTP_FROM=noreply@seudominio.com
```

---

## 📝 Configuração Passo a Passo

### 1. Criar/Editar arquivo `.env` na raiz do projeto:

```env
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seuemail@gmail.com
SMTP_PASSWORD=sua_senha_de_app
SMTP_FROM=noreply@finguia.com

# Frontend URL (para links nos emails)
FRONTEND_URL=http://localhost:3000
```

### 2. Reiniciar o backend:

```powershell
docker-compose restart backend
```

Ou se estiver rodando localmente:
```powershell
# Parar o servidor (Ctrl+C) e iniciar novamente
cd backend
uvicorn app.main:app --reload
```

### 3. Testar o Envio:

1. Acesse: http://localhost:3000/forgot-password
2. Digite um email cadastrado
3. Verifique se o email foi recebido
4. Se não receber, verifique os logs:
   ```powershell
   docker logs finguia-backend
   ```

---

## 🔍 Verificar Status Atual

Para verificar se o email está configurado:

```powershell
docker exec finguia-backend python -c "from app.core.config import settings; print('SMTP_HOST:', settings.SMTP_HOST or 'NÃO CONFIGURADO')"
```

---

## ⚠️ Modo de Desenvolvimento (SMTP Não Configurado)

Quando o SMTP **não está configurado**, o sistema:

1. ✅ Gera o token de redefinição normalmente
2. ✅ Salva no banco de dados
3. ⚠️ **NÃO envia email**
4. 📝 **Registra o link nos logs** do backend

**Para ver o link de redefinição nos logs:**
```powershell
docker logs finguia-backend | findstr "Reset link"
```

Ou:
```powershell
docker logs finguia-backend --tail 50
```

O link aparecerá assim:
```
WARNING: Reset link: http://localhost:3000/reset-password?token=eyJ...
```

**Você pode copiar esse link e usar diretamente no navegador!**

---

## 🧪 Testar Envio de Email

### Via API:

```powershell
# Solicitar redefinição de senha
curl -X POST http://localhost:8000/api/v1/auth/forgot-password `
  -H "Content-Type: application/json" `
  -d '{"email": "teste@finguia.com"}'
```

### Via Frontend:

1. Acesse: http://localhost:3000/forgot-password
2. Digite o email
3. Verifique a caixa de entrada (ou logs se não configurado)

---

## 📊 Logs e Debugging

### Ver logs do backend:
```powershell
docker logs finguia-backend --tail 100
```

### Filtrar logs de email:
```powershell
docker logs finguia-backend | findstr "email\|SMTP\|Email sent"
```

### Erros comuns:

1. **"SMTP not configured"**
   - Solução: Configure as variáveis SMTP no `.env`

2. **"Authentication failed"**
   - Solução: Verifique usuário/senha
   - Para Gmail: Use senha de app, não a senha normal

3. **"Connection timeout"**
   - Solução: Verifique firewall/proxy
   - Verifique se a porta 587 está aberta

---

## 🔒 Segurança

- ✅ Senhas nunca são enviadas por email
- ✅ Tokens expiram em 1 hora
- ✅ Links são únicos e descartáveis
- ✅ Respostas genéricas para evitar enumeração de emails

---

## 📌 Resumo

**Status Atual:** ❌ Email não configurado (modo desenvolvimento)

**Para ativar:**
1. Configure SMTP no `.env`
2. Reinicie o backend
3. Teste solicitando redefinição de senha

**Para desenvolvimento sem email:**
- Use os logs do backend para pegar o link de redefinição
- Ou configure um servidor SMTP local (MailHog, MailCatcher)

---

**Precisa de ajuda?** Consulte os logs do backend ou verifique a documentação do seu provedor de email.

