# 🚀 Deploy Rápido - EconomizeIA

## Deploy Local/Desenvolvimento

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/economizeia.git
cd economizeia

# 2. Configure variáveis de ambiente
cp .env.example .env
# Edite o .env com suas configurações

# 3. Execute o deploy
./scripts/deploy.sh
```

## Deploy em Produção (VPS)

### Passo a Passo Rápido

1. **Preparar servidor:**
```bash
ssh usuario@seu-servidor.com
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
```

2. **Clonar projeto:**
```bash
git clone https://github.com/seu-usuario/economizeia.git
cd economizeia
```

3. **Configurar .env:**
```bash
cp .env.example .env
nano .env  # Configure todas as variáveis
```

4. **Gerar SECRET_KEY:**
```bash
./scripts/generate_secret_key.sh
# Copie a chave gerada para o .env
```

5. **Build e deploy:**
```bash
./scripts/deploy.sh
```

6. **Configurar Nginx (opcional):**
```bash
sudo apt install nginx
# Configure nginx para apontar para localhost:8000
sudo certbot --nginx -d seu-dominio.com
```

## Variáveis de Ambiente Importantes

```env
# OBRIGATÓRIO - Gere uma chave forte!
SECRET_KEY=sua_chave_secreta_aqui

# Database
DATABASE_URL=postgresql://economizeia:senha@postgres:5432/economizeia_db

# SMTP (para emails)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=senha_de_app_gmail

# Frontend URL
FRONTEND_URL=https://seu-dominio.com
```

## Comandos Úteis

```bash
# Ver logs
docker-compose logs -f

# Reiniciar serviços
docker-compose restart

# Parar tudo
docker-compose down

# Atualizar código
git pull
docker-compose build
docker-compose up -d
```

## 📚 Documentação Completa

Veja `docs/DEPLOY_PRODUCAO.md` para guia completo de deploy.

