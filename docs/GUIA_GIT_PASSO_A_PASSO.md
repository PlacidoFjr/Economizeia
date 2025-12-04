# 📚 Guia Passo a Passo - Configurar Git e Fazer Upload

Este guia vai te ajudar a configurar o Git e fazer upload do projeto para o GitHub, de forma bem simples e detalhada.

## 🎯 O que vamos fazer

1. Instalar/configurar Git (se necessário)
2. Criar repositório no GitHub
3. Configurar Git no seu computador
4. Fazer upload do código

## 📋 Passo 1: Verificar se Git está instalado

Abra o PowerShell e digite:

```powershell
git --version
```

**Se aparecer uma versão** (ex: `git version 2.40.0`): ✅ Git está instalado, pule para o Passo 2.

**Se aparecer erro**: Você precisa instalar o Git.

### Instalar Git (se necessário)

1. Acesse: https://git-scm.com/download/win
2. Baixe o instalador
3. Execute e clique "Next" em tudo (deixe as opções padrão)
4. Após instalar, feche e abra o PowerShell novamente
5. Digite `git --version` para confirmar

## 📋 Passo 2: Criar Conta no GitHub (se não tiver)

1. Acesse: https://github.com
2. Clique em **"Sign up"**
3. Preencha:
   - **Username**: Escolha um nome de usuário
   - **Email**: Seu email
   - **Password**: Crie uma senha forte
4. Verifique seu email
5. Pronto! ✅

## 📋 Passo 3: Criar Repositório no GitHub

1. Faça login no GitHub
2. Clique no **"+"** no canto superior direito
3. Clique em **"New repository"**
4. Preencha:
   - **Repository name**: `economizeia` (ou outro nome)
   - **Description**: "Sistema de gestão financeira pessoal com IA"
   - **Public** ou **Private** (escolha o que preferir)
   - **NÃO marque** "Add a README file"
   - **NÃO marque** "Add .gitignore"
   - **NÃO marque** "Choose a license"
5. Clique em **"Create repository"**
6. **Copie a URL** que aparece (ex: `https://github.com/seu-usuario/economizeia.git`)

## 📋 Passo 4: Configurar Git no seu computador

Abra o PowerShell na pasta do projeto e execute:

```powershell
# Configurar seu nome (substitua pelo seu nome)
git config --global user.name "Seu Nome"

# Configurar seu email (use o mesmo do GitHub)
git config --global user.email "seu-email@gmail.com"

# Verificar se configurou corretamente
git config --global user.name
git config --global user.email
```

## 📋 Passo 5: Inicializar Git no Projeto

No PowerShell, na pasta do projeto:

```powershell
# Inicializar repositório Git
git init

# Ver status (vai mostrar todos os arquivos)
git status
```

## 📋 Passo 6: Adicionar Arquivos

```powershell
# Adicionar todos os arquivos (exceto os que estão no .gitignore)
git add .

# Ver o que foi adicionado
git status
```

## 📋 Passo 7: Fazer Primeiro Commit

```powershell
# Criar primeiro commit
git commit -m "Primeiro commit: EconomizeIA - Sistema completo"

# Ver histórico
git log --oneline
```

## 📋 Passo 8: Conectar com GitHub

```powershell
# Adicionar repositório remoto (substitua pela URL do seu repositório)
git remote add origin https://github.com/SEU-USUARIO/economizeia.git

# Verificar se conectou
git remote -v
```

## 📋 Passo 9: Fazer Upload (Push)

### Opção A: Usando Token de Acesso Pessoal (Recomendado)

O GitHub não aceita mais senha normal. Você precisa criar um **Token de Acesso Pessoal**:

1. No GitHub, clique na sua foto (canto superior direito)
2. Clique em **"Settings"**
3. No menu lateral, clique em **"Developer settings"**
4. Clique em **"Personal access tokens"** > **"Tokens (classic)"**
5. Clique em **"Generate new token"** > **"Generate new token (classic)"**
6. Preencha:
   - **Note**: "EconomizeIA Deploy"
   - **Expiration**: Escolha (90 dias ou mais)
   - **Scopes**: Marque **"repo"** (isso dá acesso completo aos repositórios)
7. Clique em **"Generate token"**
8. **COPIE O TOKEN** (você só verá ele uma vez!)
9. Guarde esse token em local seguro

Agora faça o push:

```powershell
# Fazer upload
git push -u origin main

# Quando pedir usuário: digite seu username do GitHub
# Quando pedir senha: COLE O TOKEN (não sua senha normal!)
```

**Se der erro de branch**, tente:

```powershell
# Verificar branch atual
git branch

# Se estiver em "master", renomear para "main"
git branch -M main

# Tentar push novamente
git push -u origin main
```

### Opção B: Usando GitHub CLI (Mais Fácil)

1. Instale GitHub CLI: https://cli.github.com/
2. Execute:

```powershell
# Login
gh auth login

# Seguir as instruções na tela
# Escolha: GitHub.com > HTTPS > Login with a web browser
```

Depois:

```powershell
git push -u origin main
```

## 📋 Passo 10: Verificar no GitHub

1. Acesse seu repositório no GitHub
2. Você deve ver todos os arquivos lá! ✅

## 🔄 Atualizar Código no Futuro

Sempre que fizer mudanças:

```powershell
# Ver o que mudou
git status

# Adicionar mudanças
git add .

# Fazer commit
git commit -m "Descrição do que mudou"

# Fazer upload
git push
```

## 🆘 Problemas Comuns

### Erro: "fatal: not a git repository"
**Solução**: Execute `git init` na pasta do projeto

### Erro: "remote origin already exists"
**Solução**: 
```powershell
git remote remove origin
git remote add origin https://github.com/SEU-USUARIO/economizeia.git
```

### Erro: "Authentication failed"
**Solução**: 
- Verifique se está usando o **Token** e não a senha
- Ou use GitHub CLI: `gh auth login`

### Erro: "branch 'main' does not exist"
**Solução**:
```powershell
git branch -M main
git push -u origin main
```

## ✅ Checklist

- [ ] Git instalado
- [ ] Conta GitHub criada
- [ ] Repositório criado no GitHub
- [ ] Git configurado (nome e email)
- [ ] Repositório inicializado (`git init`)
- [ ] Arquivos adicionados (`git add .`)
- [ ] Primeiro commit feito
- [ ] Repositório conectado (`git remote add origin`)
- [ ] Token de acesso criado
- [ ] Push realizado com sucesso
- [ ] Código visível no GitHub

## 🎉 Próximo Passo

Depois que o código estiver no GitHub, você pode:
1. Fazer deploy no **Vercel** (frontend)
2. Fazer deploy no **Railway** (backend)

Veja o guia: `DEPLOY_VERCEL_RAPIDO.md`

