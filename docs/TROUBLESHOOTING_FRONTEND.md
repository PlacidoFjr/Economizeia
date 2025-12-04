# 🔧 Troubleshooting - Frontend

## Erros Comuns e Soluções

### Erro: "Cannot find module" ou "Module not found"

**Causa:** Dependências não instaladas ou node_modules corrompido

**Solução:**
```powershell
cd frontend
# Limpar e reinstalar
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

### Erro: "Port 3000 is already in use"

**Causa:** Outro programa está usando a porta 3000

**Solução 1: Parar o processo**
```powershell
# Encontrar o processo
netstat -ano | findstr :3000

# Parar (substitua PID pelo número encontrado)
taskkill /PID <PID> /F
```

**Solução 2: Usar outra porta**
Edite `frontend/vite.config.ts`:
```typescript
server: {
  port: 3001,  // Mude para outra porta
}
```

### Erro: "Failed to resolve import" ou erros de TypeScript

**Causa:** Arquivos faltando ou imports incorretos

**Solução:**
```powershell
# Verificar se todos os arquivos existem
cd frontend
Get-ChildItem -Recurse src\ | Select-Object Name

# Se faltar arquivos, verifique se foram criados corretamente
```

### Erro: "Proxy error" ou "ECONNREFUSED"

**Causa:** Backend não está rodando

**Solução:**
```powershell
# Verificar se backend está rodando
docker ps | findstr backend

# Se não estiver, iniciar:
docker-compose up -d backend

# Verificar logs:
docker logs finguia-backend
```

### Erro: "SyntaxError" ou erros de compilação

**Causa:** Erro de sintaxe no código

**Solução:**
1. Verifique os erros no terminal
2. Corrija os arquivos mencionados
3. Salve e o Vite recarregará automaticamente

### Erro: "Cannot read property" ou erros de runtime

**Causa:** Dados não carregados ou API retornando erro

**Solução:**
1. Abra o DevTools do navegador (F12)
2. Vá na aba "Console" para ver erros
3. Vá na aba "Network" para ver requisições falhando
4. Verifique se a API está respondendo: http://localhost:8000/api/docs

### Erro: "CORS" ou "Access-Control-Allow-Origin"

**Causa:** Backend não está permitindo requisições do frontend

**Solução:**
Verifique se o backend está configurado para aceitar requisições de `http://localhost:3000`:
- Verifique `backend/app/main.py` - CORS_ORIGINS
- Reinicie o backend: `docker-compose restart backend`

### Erro: Página em branco

**Causa:** Erro JavaScript não tratado

**Solução:**
1. Abra DevTools (F12)
2. Veja erros no Console
3. Verifique a aba Network para requisições falhando
4. Verifique se todos os arquivos estão sendo carregados

### Erro: "npm run dev" não inicia

**Causa:** Vite não encontrado ou erro de configuração

**Solução:**
```powershell
cd frontend

# Verificar se Vite está instalado
npm list vite

# Se não estiver, instalar:
npm install vite --save-dev

# Tentar novamente:
npm run dev
```

### Erro: "TypeError: Cannot read properties of undefined"

**Causa:** Tentando acessar propriedade de objeto undefined

**Solução:**
1. Verifique o código onde o erro ocorre
2. Adicione verificações:
```typescript
// ❌ Ruim
const name = user.name

// ✅ Bom
const name = user?.name || 'Desconhecido'
```

### Erro: "401 Unauthorized" ao fazer login

**Causa:** Token inválido ou expirado

**Solução:**
1. Limpe o localStorage:
```javascript
// No console do navegador (F12):
localStorage.clear()
```
2. Faça login novamente
3. Verifique se o backend está rodando

### Erro: "Network Error" ou timeout

**Causa:** Backend não está acessível

**Solução:**
```powershell
# Verificar se backend está rodando
docker ps | findstr backend

# Verificar se porta 8000 está acessível
curl http://localhost:8000/health

# Se não funcionar, reiniciar:
docker-compose restart backend
```

---

## 🔍 Como Diagnosticar

### 1. Verificar Console do Navegador
- Pressione F12
- Vá na aba "Console"
- Veja erros em vermelho

### 2. Verificar Network
- Pressione F12
- Vá na aba "Network"
- Veja requisições falhando (vermelho)
- Clique para ver detalhes

### 3. Verificar Logs do Backend
```powershell
docker logs finguia-backend -f
```

### 4. Verificar Logs do Frontend
Os erros aparecem no terminal onde você executou `npm run dev`

---

## 💡 Dicas

1. **Sempre verifique o Console do navegador primeiro** (F12)
2. **Limpe o cache do navegador** se houver problemas estranhos
3. **Reinicie o servidor** se fizer mudanças grandes
4. **Verifique se o backend está rodando** antes de testar o frontend

---

## 📞 Ainda com Problemas?

Se nada funcionar:

1. **Limpe tudo e reinstale:**
```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
npm install
npm run dev
```

2. **Verifique versões:**
```powershell
node --version  # Deve ser 18+
npm --version
```

3. **Verifique se todos os arquivos existem:**
```powershell
Get-ChildItem -Recurse frontend\src\ | Select-Object FullName
```

---

**Lembre-se:** A maioria dos erros aparece no Console do navegador (F12)! 🔍

