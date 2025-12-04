# 🔧 Erro: "socket hang up" - Solução

## O que significa?

O erro "socket hang up" significa que o frontend tentou se conectar ao backend, mas a conexão foi fechada antes de completar.

## Causas Comuns

### 1. Backend não está rodando

**Sintoma:** Erro "socket hang up" ao tentar fazer login

**Solução:**
```powershell
# Verificar se backend está rodando
docker ps | findstr backend

# Se não estiver, iniciar:
docker-compose up -d backend

# Verificar logs:
docker logs finguia-backend
```

### 2. Backend está com erro e não inicia

**Sintoma:** Backend reinicia constantemente ou mostra erros nos logs

**Solução:**
```powershell
# Ver logs detalhados
docker logs finguia-backend --tail 50

# Se houver erro de importação, pode precisar reconstruir:
docker-compose build backend
docker-compose up -d backend
```

### 3. Porta 8000 não está acessível

**Sintoma:** Backend está rodando mas não responde

**Solução:**
```powershell
# Verificar se porta está em uso
netstat -ano | findstr :8000

# Testar conexão
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
```

### 4. Problema de proxy no Vite

**Sintoma:** Frontend não consegue fazer requisições

**Solução:**
Verifique `frontend/vite.config.ts`:
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    secure: false,  // Adicione isso
  },
}
```

## Verificação Rápida

Execute este script para diagnosticar:

```powershell
# 1. Backend rodando?
docker ps | findstr backend

# 2. Backend respondendo?
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing

# 3. Frontend na porta correta?
# Verifique qual porta o Vite está usando (pode ser 3000, 3001, 3002...)

# 4. Testar login direto na API
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -Body '{"email":"teste@finguia.com","password":"senha123"}' -ContentType "application/json" -UseBasicParsing
```

## Solução Completa

Se nada funcionar:

1. **Parar tudo:**
```powershell
docker-compose down
```

2. **Reconstruir backend:**
```powershell
docker-compose build --no-cache backend
```

3. **Iniciar tudo:**
```powershell
docker-compose up -d
```

4. **Aguardar alguns segundos** para serviços iniciarem

5. **Verificar logs:**
```powershell
docker logs finguia-backend
```

6. **Testar backend:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
```

7. **Reiniciar frontend:**
```powershell
cd frontend
npm run dev
```

## Erro Específico: ImportError no Backend

Se você vê erros como:
```
ImportError: cannot import name 'X' from 'Y'
```

**Solução:**
1. Verifique se todos os arquivos existem
2. Reconstrua a imagem:
```powershell
docker-compose build --no-cache backend
docker-compose up -d backend
```

---

**Lembre-se:** O backend precisa estar rodando e respondendo antes do frontend funcionar! ✅

