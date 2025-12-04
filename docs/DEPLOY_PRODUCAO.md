# 🚀 Guia de Deploy em Produção - EconomizeIA

Este guia explica como publicar o EconomizeIA em produção.

## 📋 Pré-requisitos

- Servidor VPS (DigitalOcean, AWS, Linode, etc) ou serviço de cloud
- Domínio (opcional, mas recomendado)
- Acesso SSH ao servidor
- Docker e Docker Compose instalados no servidor

## 🎯 Opções de Deploy

### Opção 1: Deploy em VPS (Recomendado)

#### 1. Preparar o Servidor

```bash
# Conectar ao servidor via SSH
ssh usuario@seu-servidor.com

# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
```

#### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env` no servidor:

```bash
# Database
DATABASE_URL=postgresql://economizeia:SUA_SENHA_FORTE_AQUI@postgres:5432/economizeia_db

# Security (GERE UMA CHAVE FORTE!)
SECRET_KEY=GERE_UMA_CHAVE_SECRETA_FORTE_AQUI_USE_openssl_rand_hex_32

# Redis
REDIS_URL=redis://redis:6379/0

# Ollama (se usar)
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen2.5:7b

# Google Gemini (opcional)
GEMINI_API_KEY=sua_chave_gemini_aqui
USE_GEMINI=true
GEMINI_MODEL=gemini-2.0-flash

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=GERE_UMA_SENHA_FORTE_AQUI
MINIO_BUCKET_NAME=economizeia-documents

# SMTP (Gmail ou outro)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua_senha_de_app_gmail
SMTP_FROM=noreply@economizeia.com

# Frontend URL (seu domínio)
FRONTEND_URL=https://economizeia.com

# CORS (seu domínio)
CORS_ORIGINS=["https://economizeia.com","https://www.economizeia.com"]
```

#### 3. Clonar e Configurar o Projeto

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/economizeia.git
cd economizeia

# Copiar .env
cp .env.example .env
nano .env  # Editar com suas configurações
```

#### 4. Atualizar docker-compose.yml para Produção

Crie um `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: economizeia-postgres
    environment:
      POSTGRES_USER: economizeia
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: economizeia_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - economizeia-network

  redis:
    image: redis:7-alpine
    container_name: economizeia-redis
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - economizeia-network

  minio:
    image: minio/minio:latest
    container_name: economizeia-minio
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    restart: unless-stopped
    networks:
      - economizeia-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: economizeia-backend
    env_file:
      - .env
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis
      - minio
    restart: unless-stopped
    networks:
      - economizeia-network
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: economizeia-celery-worker
    env_file:
      - .env
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - economizeia-network
    command: celery -A app.celery_app worker --loglevel=info

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: economizeia-celery-beat
    env_file:
      - .env
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - economizeia-network
    command: celery -A app.celery_app beat --loglevel=info

  nginx:
    image: nginx:alpine
    container_name: economizeia-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - economizeia-network

volumes:
  postgres_data:
  redis_data:
  minio_data:

networks:
  economizeia-network:
    driver: bridge
```

#### 5. Configurar Nginx

Crie `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name economizeia.com www.economizeia.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS Server
    server {
        listen 443 ssl http2;
        server_name economizeia.com www.economizeia.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Frontend
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # API Backend
        location /api {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

#### 6. Build do Frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

#### 7. Iniciar Serviços

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Opção 2: Deploy com Nginx Reverso (Sem Container)

#### 1. Instalar Nginx no Servidor

```bash
sudo apt install nginx certbot python3-certbot-nginx
```

#### 2. Configurar Nginx

Crie `/etc/nginx/sites-available/economizeia`:

```nginx
server {
    listen 80;
    server_name economizeia.com www.economizeia.com;

    # Frontend
    location / {
        root /var/www/economizeia/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API Backend
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/economizeia /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 3. Configurar SSL com Let's Encrypt

```bash
sudo certbot --nginx -d economizeia.com -d www.economizeia.com
```

### Opção 3: Deploy em Plataformas Cloud

#### Vercel (Frontend) + Railway/Render (Backend)

**Frontend (Vercel):**
```bash
cd frontend
npm install -g vercel
vercel
```

**Backend (Railway):**
1. Conecte seu repositório GitHub
2. Configure variáveis de ambiente
3. Railway detecta automaticamente e faz deploy

#### Render.com (Full Stack)

1. Conecte repositório GitHub
2. Configure serviços:
   - Web Service (Backend)
   - Background Worker (Celery)
   - PostgreSQL Database
   - Redis
3. Configure variáveis de ambiente

## 🔐 Segurança em Produção

### 1. Gerar SECRET_KEY Forte

```bash
openssl rand -hex 32
```

### 2. Configurar Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. Atualizar Configurações

No `backend/app/core/config.py`:

```python
ENVIRONMENT: str = "production"
DEBUG: bool = False
LOG_LEVEL: str = "WARNING"
```

### 4. Backup Automático

Crie script `backup.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec economizeia-postgres pg_dump -U economizeia economizeia_db > backup_$DATE.sql
# Enviar para S3 ou outro storage
```

## 📊 Monitoramento

### 1. Logs

```bash
# Ver logs do backend
docker logs -f economizeia-backend

# Ver logs do Celery
docker logs -f economizeia-celery-worker
docker logs -f economizeia-celery-beat
```

### 2. Health Check

Configure endpoint de health check:

```python
# backend/app/main.py
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "database": check_db(),
        "redis": check_redis()
    }
```

## 🚀 Comandos Úteis

```bash
# Ver status dos containers
docker-compose ps

# Reiniciar serviços
docker-compose restart

# Ver logs
docker-compose logs -f

# Atualizar código
git pull
docker-compose build
docker-compose up -d

# Backup do banco
docker exec economizeia-postgres pg_dump -U economizeia economizeia_db > backup.sql

# Restaurar backup
docker exec -i economizeia-postgres psql -U economizeia economizeia_db < backup.sql
```

## 📝 Checklist de Deploy

- [ ] Servidor configurado com Docker
- [ ] Variáveis de ambiente configuradas
- [ ] SECRET_KEY gerada e segura
- [ ] Banco de dados configurado
- [ ] SMTP configurado
- [ ] Frontend buildado (`npm run build`)
- [ ] Nginx configurado
- [ ] SSL/HTTPS configurado
- [ ] Firewall configurado
- [ ] Backup automático configurado
- [ ] Monitoramento configurado
- [ ] Domínio apontando para servidor

## 🆘 Troubleshooting

### Erro de conexão com banco
- Verifique `DATABASE_URL` no `.env`
- Verifique se o container do postgres está rodando

### Emails não estão sendo enviados
- Verifique configurações SMTP
- Para Gmail, use "Senha de App" (não a senha normal)

### Frontend não carrega
- Verifique se `npm run build` foi executado
- Verifique configuração do Nginx
- Verifique CORS no backend

## 📚 Recursos Adicionais

- [Docker Documentation](https://docs.docker.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
- [DigitalOcean Deploy Guide](https://www.digitalocean.com/community/tutorials)

