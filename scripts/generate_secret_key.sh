#!/bin/bash

# Script para gerar SECRET_KEY segura
# Uso: ./scripts/generate_secret_key.sh

echo "Gerando SECRET_KEY segura..."
SECRET_KEY=$(openssl rand -hex 32)
echo ""
echo "SECRET_KEY gerada:"
echo "$SECRET_KEY"
echo ""
echo "Adicione esta chave ao seu arquivo .env:"
echo "SECRET_KEY=$SECRET_KEY"

