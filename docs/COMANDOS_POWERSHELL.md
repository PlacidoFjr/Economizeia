# 💻 Comandos PowerShell - FinGuia

Guia de comandos específicos para Windows PowerShell.

## ⚠️ Diferenças entre PowerShell e Bash

O PowerShell tem algumas diferenças importantes em relação ao Bash:

1. **Redirecionamento:** Não usa `<` da mesma forma
2. **Aspas:** Precisa escapar caracteres especiais
3. **Comandos SQL:** Alguns comandos precisam ser adaptados

---

## 📋 Comandos Essenciais

### Criar Banco de Dados

**❌ NÃO funciona no PowerShell:**
```bash
docker exec -i finguia-postgres psql -U finguia -d finguia_db < backend/app/db/schema.sql
```

**✅ Funciona no PowerShell:**
```powershell
Get-Content backend/app/db/schema.sql | docker exec -i finguia-postgres psql -U finguia -d finguia_db
```

**Ou use o script:**
```powershell
.\scripts\criar_banco.ps1
```

### Verificar Tabelas

**❌ Pode abrir nova janela no PowerShell:**
```bash
docker exec -it finguia-postgres psql -U finguia -d finguia_db -c "\dt"
```

**✅ Funciona no PowerShell (sem -it para comandos não-interativos):**
```powershell
docker exec finguia-postgres psql -U finguia -d finguia_db -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"
```

**💡 Dica:** No PowerShell, use `-it` apenas quando realmente precisar de modo interativo. Para comandos simples, use sem `-it`.

**Ou use o script:**
```powershell
.\scripts\verificar_banco.ps1
```

### Conectar ao Banco Interativamente

```powershell
docker exec -it finguia-postgres psql -U finguia -d finguia_db
```

Depois você pode usar comandos SQL normalmente:
- `\dt` - Listar tabelas
- `\d users` - Ver estrutura da tabela users
- `SELECT * FROM users;` - Consultar dados
- `\q` - Sair

### Ver Logs

```powershell
docker logs finguia-backend
docker logs finguia-backend -f  # Seguir logs em tempo real
```

### Parar Serviços

```powershell
docker-compose down
```

### Iniciar Serviços

```powershell
docker-compose up -d
```

### Reiniciar um Serviço

```powershell
docker-compose restart backend
```

### Ver Status dos Containers

```powershell
docker ps
docker ps -a  # Inclui containers parados
```

### Executar Comandos Dentro de Containers

**Comandos não-interativos (sem -it):**
```powershell
docker exec finguia-backend python --version
docker exec finguia-postgres psql -U finguia -d finguia_db -c "SELECT COUNT(*) FROM users;"
```

**Modo interativo (com -it):**
```powershell
docker exec -it finguia-backend bash
docker exec -it finguia-postgres psql -U finguia -d finguia_db
```

**⚠️ Nota:** No PowerShell, `-it` pode abrir uma nova janela. Se isso acontecer, tente usar `cmd` ao invés de PowerShell ou use comandos sem `-it`.

### Limpar Tudo

```powershell
docker-compose down -v  # Remove volumes também
docker system prune -a  # Remove imagens não usadas
```

---

## 🔧 Scripts Disponíveis

### Criar Banco de Dados
```powershell
.\scripts\criar_banco.ps1
```

### Verificar Banco
```powershell
.\scripts\verificar_banco.ps1
```

### Verificar Ollama
```powershell
.\scripts\verificar_ollama.bat
```

---

## 🐛 Problemas Comuns

### Erro: "Operador '<' reservado"

**Causa:** Tentou usar redirecionamento bash no PowerShell

**Solução:** Use `Get-Content` ao invés de `<`:
```powershell
# ❌ Errado
docker exec ... < arquivo.sql

# ✅ Correto
Get-Content arquivo.sql | docker exec -i ...
```

### Erro: "Token inesperado"

**Causa:** Comandos bash sendo interpretados pelo PowerShell

**Solução:** Use comandos PowerShell ou scripts `.ps1`

### Erro: "Comando não encontrado"

**Causa:** Tentou executar comando bash diretamente

**Solução:** Use `docker exec` para executar dentro do container

---

## 💡 Dicas

1. **Use scripts `.ps1`:** Mais fácil e confiável
2. **Verifique sintaxe:** PowerShell é case-insensitive mas precisa de aspas corretas
3. **Use `-it` com cuidado:** Alguns comandos funcionam melhor sem `-it` no PowerShell
4. **Prefira comandos SQL:** Ao invés de comandos `\dt`, use `SELECT` statements

---

## 📚 Referências

- [PowerShell Documentation](https://docs.microsoft.com/powershell/)
- [Docker PowerShell](https://docs.docker.com/desktop/windows/powershell/)

