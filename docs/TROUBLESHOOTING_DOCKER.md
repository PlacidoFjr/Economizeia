# 🔧 Troubleshooting - Problemas com Docker

## Erro: "Read timed out" ao construir imagem

### O que significa?

O Docker está tentando baixar pacotes Python do PyPI (repositório de pacotes), mas a conexão está demorando muito ou caindo.

### Soluções

#### Solução 1: Tentar Novamente (Mais Simples)

Muitas vezes é um problema temporário de rede. Tente novamente:

```bash
docker-compose build --no-cache
```

ou

```bash
docker-compose up -d --build
```

#### Solução 2: Aumentar Timeout (Já Implementado)

O Dockerfile já foi atualizado para usar timeout maior. Se ainda der erro, você pode editar manualmente:

```dockerfile
# No arquivo backend/Dockerfile, linha 17
RUN pip install --no-cache-dir --default-timeout=100 --retries=5 -r requirements.txt
```

#### Solução 3: Usar Mirror do PyPI (China/Brasil)

Se você está em uma região com conexão lenta, use um mirror:

**Edite `backend/Dockerfile`:**

```dockerfile
# Adicione antes do RUN pip install:
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
# ou para Brasil:
# RUN pip config set global.index-url https://pypi.org/simple
```

#### Solução 4: Instalar Localmente Primeiro

Instale as dependências localmente e depois copie:

```bash
cd backend
pip install -r requirements.txt
```

Depois modifique o Dockerfile para não reinstalar (não recomendado para produção).

#### Solução 5: Build em Etapas

Modifique o `backend/Dockerfile` para instalar em etapas:

```dockerfile
# Instalar dependências mais leves primeiro
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy

# Depois as mais pesadas
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt
```

#### Solução 6: Usar Cache do Docker

Se você já construiu antes, use o cache:

```bash
docker-compose build
```

#### Solução 7: Verificar Conexão

Teste sua conexão com o PyPI:

```bash
curl -I https://pypi.org/simple/
```

Se não responder, pode ser problema de firewall/proxy.

---

## Erro: "Port already in use"

### Solução:

```bash
# Parar todos os containers
docker-compose down

# Verificar portas em uso
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Mac/Linux

# Se necessário, altere as portas no docker-compose.yml
```

---

## Erro: "Cannot connect to Docker daemon"

### Solução:

1. **Verifique se o Docker Desktop está rodando**
   - Windows/Mac: Abra o Docker Desktop
   - Linux: `sudo systemctl start docker`

2. **Reinicie o Docker Desktop**

3. **Verifique permissões (Linux):**
   ```bash
   sudo usermod -aG docker $USER
   # Faça logout e login novamente
   ```

---

## Erro: "No space left on device"

### Solução:

```bash
# Limpar imagens não usadas
docker system prune -a

# Limpar volumes
docker volume prune

# Ver espaço usado
docker system df
```

---

## Erro: Build muito lento

### Soluções:

1. **Use cache do Docker:**
   ```bash
   docker-compose build
   ```

2. **Build apenas um serviço:**
   ```bash
   docker-compose build backend
   ```

3. **Use .dockerignore:**
   Certifique-se de que `backend/.dockerignore` existe e exclui arquivos desnecessários.

---

## Container para logo após iniciar

### Verificar logs:

```bash
docker logs finguia-backend
docker logs finguia-celery-worker
```

### Verificar se o banco está acessível:

```bash
docker exec -it finguia-postgres psql -U finguia -d finguia_db -c "SELECT 1;"
```

### Verificar variáveis de ambiente:

```bash
docker exec finguia-backend env | grep DATABASE_URL
```

---

## Erro: "Module not found" dentro do container

### Solução:

1. **Rebuild sem cache:**
   ```bash
   docker-compose build --no-cache backend
   ```

2. **Verifique se requirements.txt está correto:**
   ```bash
   cat backend/requirements.txt
   ```

3. **Instale manualmente no container:**
   ```bash
   docker exec -it finguia-backend pip install <nome-do-modulo>
   ```

---

## Dicas Gerais

### Ver status de todos os containers:

```bash
docker-compose ps
```

### Ver logs em tempo real:

```bash
docker-compose logs -f
```

### Reiniciar um serviço específico:

```bash
docker-compose restart backend
```

### Reconstruir apenas um serviço:

```bash
docker-compose build backend
docker-compose up -d backend
```

### Limpar tudo e começar do zero:

```bash
docker-compose down -v
docker system prune -a
docker-compose up -d --build
```

---

## Problemas Específicos do FinGuia

### Backend não conecta ao banco:

1. Verifique se o PostgreSQL está rodando:
   ```bash
   docker ps | grep postgres
   ```

2. Verifique a DATABASE_URL no `.env`

3. Aguarde alguns segundos após iniciar (o banco precisa inicializar)

### Celery não processa tarefas:

1. Verifique se o Redis está rodando:
   ```bash
   docker ps | grep redis
   ```

2. Verifique os logs:
   ```bash
   docker logs finguia-celery-worker
   ```

### MinIO não acessível:

1. Verifique se está rodando:
   ```bash
   docker ps | grep minio
   ```

2. Acesse o console: http://localhost:9001
   - Usuário: `minioadmin`
   - Senha: `minioadmin123`

---

**Lembre-se:** A maioria dos problemas de timeout são temporários. Tente novamente após alguns minutos! 🔄

