#!/bin/bash

# Script de deploy automatizado para EconomizeIA
# Uso: ./scripts/deploy.sh

set -e

echo "🚀 Iniciando deploy do EconomizeIA..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se está no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Erro: Execute este script da raiz do projeto${NC}"
    exit 1
fi

# Verificar se .env existe
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Arquivo .env não encontrado. Criando a partir do .env.example...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Por favor, edite o arquivo .env com suas configurações antes de continuar${NC}"
        exit 1
    else
        echo -e "${RED}❌ Arquivo .env.example não encontrado${NC}"
        exit 1
    fi
fi

# Build do frontend
echo -e "${GREEN}📦 Buildando frontend...${NC}"
cd frontend
npm install
npm run build
cd ..

# Parar containers existentes
echo -e "${GREEN}🛑 Parando containers existentes...${NC}"
docker-compose down

# Build das imagens
echo -e "${GREEN}🔨 Buildando imagens Docker...${NC}"
docker-compose build

# Iniciar serviços
echo -e "${GREEN}🚀 Iniciando serviços...${NC}"
docker-compose up -d

# Aguardar serviços iniciarem
echo -e "${GREEN}⏳ Aguardando serviços iniciarem...${NC}"
sleep 10

# Verificar status
echo -e "${GREEN}✅ Verificando status dos serviços...${NC}"
docker-compose ps

# Verificar saúde do backend
echo -e "${GREEN}🏥 Verificando saúde do backend...${NC}"
sleep 5
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend está respondendo!${NC}"
else
    echo -e "${YELLOW}⚠️  Backend pode estar ainda inicializando...${NC}"
fi

echo -e "${GREEN}🎉 Deploy concluído!${NC}"
echo -e "${GREEN}📊 Acesse: http://localhost:8000/api/docs para ver a documentação da API${NC}"

