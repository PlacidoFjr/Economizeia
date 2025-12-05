# 🔧 Railway vs Local: Variáveis de Ambiente

## ⚠️ Diferença Importante

### 🏠 **Local (Desenvolvimento)**
- Usa arquivo `.env` na raiz do projeto ou em `backend/.env`
- Variáveis são lidas do arquivo `.env`

### 🌐 **Railway (Produção)**
- **NÃO usa arquivo `.env`**
- Variáveis vêm das **Environment Variables** configuradas no Railway Dashboard
- As variáveis do Railway **sempre têm prioridade** sobre qualquer `.env`

## 🔍 Como Funciona a Prioridade

O `pydantic-settings` carrega variáveis nesta ordem (maior prioridade primeiro):

1. **Variáveis de ambiente do sistema** (Railway) ← **MAIOR PRIORIDADE**
2. Arquivo `.env` (apenas local)
3. Valores padrão no código

## ✅ Verificar Configuração no Railway

### 1. Acesse o Railway Dashboard
- Vá em: https://railway.app
- Selecione seu projeto: **economizeia-production**

### 2. Verifique as Variáveis
- Vá em **Variables** (ou **Settings** → **Variables**)
- Verifique se TODAS as variáveis necessárias estão configuradas

### 3. Variáveis Essenciais

#### Obrigatórias:
- `DATABASE_URL` - URL do PostgreSQL do Railway
- `REDIS_URL` - URL do Redis do Railway
- `SECRET_KEY` - Chave secreta para JWT
- `CORS_ORIGINS` - URLs permitidas (ex: `["https://economizeia.vercel.app"]`)
- `FRONTEND_URL` - URL do frontend (ex: `https://economizeia.vercel.app`)

#### Opcionais (mas recomendadas):
- `SMTP_HOST` - Servidor SMTP
- `SMTP_PORT` - Porta SMTP (geralmente 587)
- `SMTP_USER` - Email do SMTP
- `SMTP_PASSWORD` - Senha do SMTP
- `GEMINI_API_KEY` - Chave da API do Gemini (para chatbot)
- `USE_GEMINI` - `true` ou `false`

## 🔍 Verificar se Está Funcionando

### 1. Verifique os Logs do Railway
- Railway Dashboard → **Deploy Logs**
- Procure por:
  ```
  ==================================================
  Configurações carregadas:
    DATABASE_URL: ✅ Configurado
    REDIS_URL: ✅ Configurado
    SMTP_HOST: ✅ Configurado
    ...
  ==================================================
  ```

### 2. Se Aparecer "⚠️ Usando padrão local"
- Significa que a variável **não está configurada no Railway**
- Configure ela nas **Variables** do Railway

### 3. Se Aparecer "❌ Não configurado"
- A variável não está configurada (mas pode ser opcional)
- Se for obrigatória, configure no Railway

## 🚨 Problema Comum

### "Funcionava localmente mas não no Railway"

**Causa:** Variáveis estão no `.env` local mas não foram configuradas no Railway.

**Solução:**
1. Abra seu `.env` local
2. Copie as variáveis importantes
3. Configure no Railway Dashboard → **Variables**
4. Faça redeploy

## 📋 Checklist

- [ ] `DATABASE_URL` configurada no Railway
- [ ] `REDIS_URL` configurada no Railway
- [ ] `SECRET_KEY` configurada no Railway
- [ ] `CORS_ORIGINS` configurada no Railway
- [ ] `FRONTEND_URL` configurada no Railway
- [ ] `SMTP_*` configuradas no Railway (se usar email)
- [ ] `GEMINI_API_KEY` configurada no Railway (se usar chatbot)
- [ ] Logs do Railway mostram "✅ Configurado" para variáveis importantes

## 💡 Dica

**Nunca commite o arquivo `.env` no Git!** Ele deve estar no `.gitignore`.

As variáveis sensíveis devem ser configuradas apenas no Railway Dashboard.

