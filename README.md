# 💰 EconomizeIA

Sistema de gestão financeira pessoal com IA, OCR e notificações automáticas.

## 🚀 Funcionalidades

- 📄 **Upload de Boletos com OCR**: Envie seus boletos e faturas, nossa IA extrai as informações automaticamente
- 🤖 **Assistente Virtual Inteligente**: Chatbot com IA (Gemini/Ollama) para ajudar com suas finanças
- 📊 **Dashboard Completo**: Visualize receitas, despesas, gráficos e análises
- 🔔 **Notificações Automáticas**: Alertas por email quando extrapolar receita ou pagamentos próximos
- 💳 **Gestão de Finanças**: Separação entre boletos e outras transações financeiras
- 📅 **Agendamento de Pagamentos**: Organize seus pagamentos e receba lembretes
- 🔐 **Segurança**: Autenticação JWT, verificação de email, LGPD compliant

## 🛠️ Tecnologias

- **Backend**: FastAPI (Python), PostgreSQL, Redis, Celery
- **Frontend**: React, TypeScript, Tailwind CSS, Vite
- **IA**: Google Gemini API ou Ollama (local)
- **OCR**: Tesseract, OCRmyPDF
- **Storage**: MinIO (S3 compatible)

## 📦 Instalação

### Pré-requisitos

- Docker e Docker Compose
- Node.js 18+ e npm
- Python 3.11+ (para desenvolvimento local)

### Configuração Rápida

1. **Clone o repositório**
```bash
git clone https://github.com/seu-usuario/economizeia.git
cd economizeia
```

2. **Configure variáveis de ambiente**
```bash
# Copie o arquivo de exemplo
cp backend/.env.example backend/.env

# Edite o .env com suas configurações
nano backend/.env
```

3. **Inicie os serviços**
```bash
docker-compose up -d
```

4. **Acesse a aplicação**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

## 🔧 Configuração

### Variáveis de Ambiente Importantes

```env
# Security (OBRIGATÓRIO - gere uma chave forte!)
SECRET_KEY=sua-chave-secreta-aqui

# Database
DATABASE_URL=postgresql://economizeia:economizeia_dev@postgres:5432/economizeia_db

# SMTP (para emails)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=senha-de-app-gmail

# Google Gemini (opcional)
GEMINI_API_KEY=sua-chave-gemini
USE_GEMINI=true
```

### Gerar SECRET_KEY

```bash
openssl rand -hex 32
```

## 📚 Documentação

- [Guia de Deploy no Vercel](DEPLOY_VERCEL_RAPIDO.md)
- [Guia Completo de Deploy](docs/DEPLOY_PRODUCAO.md)
- [Configurar Git e GitHub](docs/GUIA_GIT_PASSO_A_PASSO.md)
- [Configurar Gemini](docs/CONFIGURAR_GEMINI.md)
- [Troubleshooting](docs/TROUBLESHOOTING_FRONTEND.md)

## 🚀 Deploy

### Vercel + Railway (Recomendado)

1. **Frontend no Vercel**: Veja [DEPLOY_VERCEL_RAPIDO.md](DEPLOY_VERCEL_RAPIDO.md)
2. **Backend no Railway**: Conecte seu repositório GitHub
3. Configure variáveis de ambiente em cada plataforma

## 📝 Estrutura do Projeto

```
economizeia/
├── backend/          # API FastAPI
│   ├── app/
│   │   ├── api/      # Endpoints
│   │   ├── services/ # Serviços (OCR, IA, etc)
│   │   └── db/       # Modelos e database
│   └── requirements.txt
├── frontend/         # React + TypeScript
│   ├── src/
│   │   ├── pages/    # Páginas
│   │   ├── components/
│   │   └── services/
│   └── package.json
└── docker-compose.yml
```

## 🔐 Segurança

- ✅ `.env` está no `.gitignore` (não será commitado)
- ✅ Use `.env.example` como referência
- ✅ Gere SECRET_KEY forte para produção
- ✅ Configure CORS adequadamente
- ✅ Use HTTPS em produção

## 📄 Licença

Este projeto é privado. Todos os direitos reservados.

## 👥 Contribuindo

Este é um projeto privado. Para questões ou sugestões, abra uma issue.

---

**EconomizeIA** - Organize suas finanças com inteligência artificial 🚀
