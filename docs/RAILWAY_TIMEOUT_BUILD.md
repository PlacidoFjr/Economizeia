# ⏱️ Como Resolver Timeout no Build do Railway

## ❌ Problema

O build no Railway está dando **"Build timed out"**. Isso acontece quando o build demora mais de 10-15 minutos.

**Causas comuns:**
- Instalação de dependências do sistema (apt-get) muito lenta
- Instalação de dependências Python muito lenta
- Contexto de build muito grande (muitos arquivos sendo copiados)
- Problemas de rede durante o download

---

## ✅ Solução 1: Otimizar Dockerfile (JÁ FEITO!)

O Dockerfile já foi otimizado com:
- ✅ Timeout aumentado para 300 segundos
- ✅ Retry aumentado para 10 tentativas
- ✅ Cache de camadas melhorado
- ✅ Dependências do sistema otimizadas

**Se ainda der timeout, tente as soluções abaixo:**

---

## ✅ Solução 2: Reduzir Contexto de Build

O `.dockerignore` já está configurado, mas verifique se não há arquivos grandes sendo copiados:

1. Verifique o tamanho do repositório:
   ```bash
   git ls-files | wc -l
   ```

2. Se houver muitos arquivos, adicione ao `.dockerignore`:
   - Arquivos de log grandes
   - Arquivos de backup
   - Arquivos temporários

---

## ✅ Solução 3: Usar Build Cache do Railway

O Railway mantém cache entre builds. Se o build falhar:

1. **NÃO** limpe o cache imediatamente
2. Tente fazer deploy novamente (o cache pode ajudar)
3. Se continuar falhando, aí sim limpe o cache:
   - No Railway, vá em **Settings** do serviço
   - Procure por **"Clear Build Cache"**
   - Clique e faça novo deploy

---

## ✅ Solução 4: Dividir Build em Etapas

Se o problema persistir, podemos criar um Dockerfile multi-stage:

1. **Stage 1**: Instalar apenas dependências do sistema
2. **Stage 2**: Instalar dependências Python
3. **Stage 3**: Copiar código da aplicação

Isso permite melhor cache e builds mais rápidos.

---

## ✅ Solução 5: Usar Imagem Base Mais Leve

Se ainda der timeout, podemos usar uma imagem base mais leve:

- `python:3.11-alpine` (muito menor, mas pode ter problemas com algumas dependências)
- Ou manter `python:3.11-slim` (já é otimizada)

---

## ✅ Solução 6: Verificar Dependências Pesadas

Algumas dependências são muito pesadas:

- `ocrmypdf` - requer muitas dependências do sistema
- `pytesseract` - requer Tesseract OCR
- `pillow` - pode ser pesado
- `cryptography` - pode demorar para compilar

**Se não estiver usando OCR no momento**, podemos torná-lo opcional.

---

## 🚀 Solução Rápida (Tente Primeiro!)

### Passo 1: Verificar Configurações do Railway

1. No Railway, vá no serviço do backend
2. Vá em **Settings** → **Build**
3. Verifique se:
   - **Root Directory**: está vazio ou `.`
   - **Dockerfile Path**: está como `backend/Dockerfile`
   - **Build Command**: está vazio (usa Dockerfile)

### Passo 2: Limpar Cache e Fazer Novo Deploy

1. No Railway, vá em **Settings** do serviço
2. Procure por **"Clear Build Cache"** ou **"Clear Cache"**
3. Clique para limpar
4. Vá em **Deployments**
5. Clique nos **3 pontinhos** (⋯) do último deploy
6. Clique em **"Redeploy"**
7. Aguarde (pode demorar 5-10 minutos na primeira vez)

### Passo 3: Monitorar o Build

1. Durante o build, acompanhe os logs
2. Veja em qual etapa está travando:
   - Se for em `apt-get update` → problema de rede
   - Se for em `pip install` → dependências pesadas
   - Se for em `COPY backend/` → contexto muito grande

---

## 🔍 Diagnóstico

### Como saber qual etapa está travando?

Nos logs do Railway, você verá:

```
1. FROM python:3.11-slim
2. WORKDIR /app
3. RUN apt-get update...  ← Se travar aqui, é problema de rede/apt
4. RUN pip install...     ← Se travar aqui, são dependências Python
5. COPY backend/...      ← Se travar aqui, é contexto grande
```

**Identifique a etapa e me avise!**

---

## 💡 Dicas

1. **Primeira build sempre demora mais** - Railway precisa baixar todas as imagens base
2. **Builds subsequentes são mais rápidos** - Cache ajuda muito
3. **Evite fazer deploy durante horários de pico** - Pode ter mais latência
4. **Se der timeout, tente novamente** - Pode ser problema temporário de rede

---

## 🆘 Se Nada Funcionar

Se após tentar todas as soluções ainda der timeout:

1. **Verifique se há arquivos muito grandes no repositório:**
   ```bash
   find . -type f -size +10M
   ```

2. **Considere usar Railway Buildpacks** em vez de Dockerfile:
   - Railway pode detectar automaticamente Python
   - Mas você perde controle sobre dependências do sistema (OCR)

3. **Entre em contato com suporte do Railway:**
   - Eles podem aumentar o timeout para seu projeto
   - Ou investigar problemas de infraestrutura

---

## 📋 Checklist

- [ ] Dockerfile otimizado (já feito ✅)
- [ ] `.dockerignore` configurado (já feito ✅)
- [ ] Cache limpo e novo deploy tentado
- [ ] Logs verificados para identificar etapa problemática
- [ ] Dependências pesadas identificadas
- [ ] Build funcionando! ✅

---

**Próximo passo:** Tente fazer um novo deploy e me avise em qual etapa está travando!

