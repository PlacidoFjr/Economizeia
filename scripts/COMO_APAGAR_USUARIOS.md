# Como Apagar Todos os Usuários do Banco

## 🚀 Forma Mais Simples: Via Railway CLI

### 1. Conectar ao PostgreSQL

```bash
railway connect postgres
```

### 2. Executar o SQL

Cole e execute:

```sql
DELETE FROM audit_logs;
DELETE FROM notifications;
DELETE FROM savings_goals;
DELETE FROM investments;
DELETE FROM payments;
DELETE FROM bills;
DELETE FROM users;
```

### 3. Verificar

```sql
SELECT COUNT(*) as total_usuarios FROM users;
```

Deve retornar `0`.

---

## 🔧 Alternativa: Script Python

Execute:

```bash
python scripts/reset_users_railway.py
```

O script vai pedir:
1. A `DATABASE_URL` do Railway
2. Confirmação digitando "SIM"

---

## ⚠️ ATENÇÃO

Isso apaga **TODOS** os dados:
- ✅ Todos os usuários
- ✅ Todos os boletos/finanças
- ✅ Todas as metas de economia
- ✅ Todos os investimentos
- ✅ Todos os pagamentos
- ✅ Todas as notificações
- ✅ Todos os logs de auditoria

**Não tem como desfazer!**

