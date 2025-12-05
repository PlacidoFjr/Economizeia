# Como Apagar Todos os Usuários - Forma Mais Simples

## 🚀 Solução: Endpoint Temporário no Backend

Criei um endpoint temporário que você pode chamar diretamente!

### Passo 1: Fazer Deploy

Faça commit e push das alterações para o Railway fazer deploy.

### Passo 2: Chamar o Endpoint

Depois do deploy, acesse no navegador ou via curl:

```
POST https://seu-backend.railway.app/api/v1/reset-all-users
```

**Ou via PowerShell:**

```powershell
Invoke-WebRequest -Uri "https://seu-backend.railway.app/api/v1/reset-all-users" -Method POST
```

**Ou via curl:**

```bash
curl -X POST https://seu-backend.railway.app/api/v1/reset-all-users
```

### Passo 3: Verificar Resposta

Você deve receber:

```json
{
  "status": "success",
  "message": "Todos os dados foram apagados!",
  "usuarios_restantes": 0,
  "boletos_restantes": 0
}
```

### ⚠️ IMPORTANTE: Remover o Endpoint Depois!

Após usar, **remova o endpoint** de `backend/app/main.py` (linhas 62-120 aproximadamente).

---

## 🔧 Alternativa: Script Python

Se preferir usar o script:

1. No Railway, copie a `DATABASE_URL` (Postgres → Variables → DATABASE_URL)
2. Execute:

```bash
python scripts/reset_users_railway.py
```

3. Cole a `DATABASE_URL` quando pedir
4. Digite "SIM" para confirmar

