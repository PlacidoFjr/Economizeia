# 🚀 Deploy Rápido no Vercel - EconomizeIA

## ⚡ Deploy em 5 Minutos

### 1. Frontend no Vercel

```bash
# 1. Instalar Vercel CLI
npm i -g vercel

# 2. Entrar no diretório do frontend
cd frontend

# 3. Login no Vercel
vercel login

# 4. Deploy
vercel

# 5. Deploy em produção
vercel --prod
```

**OU via GitHub (Mais fácil):**

1. Faça push do código para GitHub
2. Acesse [vercel.com](https://vercel.com) e faça login
3. Clique em **"Add New Project"**
4. Importe seu repositório
5. Configure:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
6. Adicione variável de ambiente:
   - **Name**: `VITE_API_URL`
   - **Value**: `https://seu-backend.railway.app/api/v1` (você vai configurar depois)
7. Clique em **"Deploy"**

### 2. Backend no Railway (Gratuito)

1. Acesse [railway.app](https://railway.app)
2. Faça login com GitHub
3. Clique em **"New Project"**
4. Selecione **"Deploy from GitHub repo"**
5. Escolha seu repositório
6. Railway detecta automaticamente e faz deploy
7. Adicione serviços:
   - **PostgreSQL**: Clique em "+ New" > "Database" > "PostgreSQL"
   - **Redis**: Clique em "+ New" > "Database" > "Redis"
8. Configure variáveis de ambiente:
   - `DATABASE_URL`: Copie da variável do PostgreSQL
   - `REDIS_URL`: Copie da variável do Redis
   - `SECRET_KEY`: Gere com `openssl rand -hex 32`
   - `SMTP_HOST`: `smtp.gmail.com`
   - `SMTP_PORT`: `587`
   - `SMTP_USER`: Seu email Gmail
   - `SMTP_PASSWORD`: Senha de app do Gmail
   - `FRONTEND_URL`: URL do Vercel (ex: `https://economizeia.vercel.app`)
   - `CORS_ORIGINS`: `["https://economizeia.vercel.app"]`
9. Copie a URL do backend (ex: `https://economizeia-backend.railway.app`)
10. Volte no Vercel e atualize `VITE_API_URL` com a URL do Railway

### 3. Configurar Celery (Worker e Beat)

No Railway, adicione 2 novos serviços:

**Worker:**
1. "+ New" > "Empty Service"
2. Conecte ao mesmo repositório
3. Configure:
   - **Start Command**: `celery -A app.celery_app worker --loglevel=info`
   - Mesmas variáveis de ambiente do backend

**Beat:**
1. "+ New" > "Empty Service"
2. Conecte ao mesmo repositório
3. Configure:
   - **Start Command**: `celery -A app.celery_app beat --loglevel=info`
   - Mesmas variáveis de ambiente do backend

## ✅ Pronto!

Agora você tem:
- ✅ Frontend rodando no Vercel
- ✅ Backend rodando no Railway
- ✅ Banco de dados PostgreSQL
- ✅ Redis para cache
- ✅ Celery para tarefas em background
- ✅ Tudo funcionando automaticamente!

## 🔗 URLs

- **Frontend**: `https://seu-app.vercel.app`
- **Backend API**: `https://seu-backend.railway.app`
- **API Docs**: `https://seu-backend.railway.app/api/docs`

## 📝 Checklist Final

- [ ] Frontend deployado no Vercel
- [ ] Backend deployado no Railway
- [ ] PostgreSQL adicionado
- [ ] Redis adicionado
- [ ] Celery Worker configurado
- [ ] Celery Beat configurado
- [ ] Variáveis de ambiente configuradas
- [ ] `VITE_API_URL` apontando para Railway
- [ ] CORS configurado no backend
- [ ] Testar login/registro
- [ ] Testar chatbot
- [ ] Testar upload de boletos

## 🆘 Problemas Comuns

### Frontend não conecta com backend
- Verifique `VITE_API_URL` no Vercel
- Verifique CORS no backend
- Verifique se backend está online

### Erro 404 no Vercel
- Verifique se `dist/` está sendo gerado
- Verifique build logs no Vercel
- Verifique `vercel.json`

### Backend não inicia
- Verifique logs no Railway
- Verifique variáveis de ambiente
- Verifique se `DATABASE_URL` está correto

## 💰 Custos

- **Vercel**: Gratuito para projetos pessoais
- **Railway**: $5 crédito grátis/mês (suficiente para começar)
- **Total**: **GRÁTIS** para começar! 🎉

