# Erro de Container no Railway - Solução

## Erro
```
Container failed to start
ctrd: failed to pull image: failed to prepare extraction snapshot
failed to open database file: open /var/lib/containers/containerd/io.containerd.snapshotter.v1.overlayfs/metadata.db: no such file or directory
```

## Causa
Este é um erro de infraestrutura do Railway relacionado ao containerd (sistema de containers). Pode ser causado por:
- Problema temporário no Railway
- Cache corrompido
- Problema com a imagem Docker base

## Soluções

### 1. Limpar Cache e Fazer Redeploy (Recomendado)
1. Acesse o Railway Dashboard
2. Vá para o seu serviço
3. Clique em **Settings** → **Deploy**
4. Clique em **Clear Build Cache**
5. Faça um novo deploy (pode ser automático após limpar cache)

### 2. Forçar Rebuild Sem Cache
No Railway Dashboard:
1. Vá para **Settings** → **Deploy**
2. Ative **"Clear Build Cache"**
3. Clique em **Redeploy**

### 3. Verificar Dockerfile
O Dockerfile está correto, mas se o problema persistir:
- Verifique se a imagem base `python:3.11-slim` está disponível
- Tente usar `python:3.11` ao invés de `python:3.11-slim` temporariamente

### 4. Contatar Suporte do Railway
Se o problema persistir após limpar o cache:
1. Acesse https://railway.app/support
2. Reporte o erro com:
   - ID do serviço
   - Logs do deploy
   - Mensagem de erro completa

### 5. Verificar Status do Railway
- Acesse https://status.railway.app
- Verifique se há incidentes reportados

## Configuração Atualizada
O arquivo `railway.toml` foi atualizado com:
- Healthcheck path (`/health`)
- Healthcheck timeout (100s)
- Comentários sobre rebuild sem cache

## Próximos Passos
1. Limpar cache no Railway Dashboard
2. Fazer redeploy
3. Verificar logs do deploy
4. Se persistir, contatar suporte do Railway

