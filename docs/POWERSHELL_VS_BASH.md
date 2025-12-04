# 🔄 Diferenças: PowerShell vs Bash

Guia rápido das principais diferenças ao usar comandos Docker no PowerShell vs Bash.

## ⚠️ Problema: `-it` no PowerShell

No PowerShell, o flag `-it` pode abrir uma nova janela ao invés de executar o comando no terminal atual.

### Solução

**Para comandos não-interativos, use SEM `-it`:**

```powershell
# ✅ Correto no PowerShell
docker exec finguia-postgres psql -U finguia -d finguia_db -c "SELECT 1;"

# ❌ Pode abrir nova janela
docker exec -it finguia-postgres psql -U finguia -d finguia_db -c "SELECT 1;"
```

**Para modo interativo, `-it` é necessário:**

```powershell
# ✅ Correto - modo interativo precisa de -it
docker exec -it finguia-postgres psql -U finguia -d finguia_db
```

---

## 📋 Comparação de Comandos

### Verificar Tabelas

| Bash | PowerShell |
|------|-----------|
| `docker exec -it ... -c "\dt"` | `docker exec ... -c "SELECT tablename FROM pg_tables..."` |

### Redirecionamento de Arquivo

| Bash | PowerShell |
|------|-----------|
| `docker exec ... < arquivo.sql` | `Get-Content arquivo.sql \| docker exec -i ...` |

### Listar Containers

| Bash | PowerShell |
|------|-----------|
| `docker ps \| grep redis` | `docker ps \| findstr redis` |

### Ver Logs

| Bash | PowerShell |
|------|-----------|
| `docker logs -f container` | `docker logs -f container` ✅ Igual |

---

## 💡 Regras Gerais

1. **Comandos simples:** Use SEM `-it` no PowerShell
2. **Modo interativo:** Use COM `-it` (pode abrir nova janela, mas é necessário)
3. **Redirecionamento:** Use `Get-Content \|` ao invés de `<`
4. **Filtros:** Use `findstr` ao invés de `grep`

---

## 🛠️ Alternativas

### Se `-it` abrir nova janela:

1. **Use scripts `.ps1`** - Mais confiável
2. **Use CMD** - `cmd /c "docker exec -it ..."`
3. **Use sem `-it`** - Para comandos não-interativos

### Exemplo de Script

```powershell
# scripts/verificar_banco.ps1
docker exec finguia-postgres psql -U finguia -d finguia_db -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
```

---

**Lembre-se:** Quando em dúvida, use os scripts `.ps1` fornecidos! ✅

