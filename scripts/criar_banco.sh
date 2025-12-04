#!/bin/bash
# Script para criar o banco de dados - Linux/Mac
# Uso: bash scripts/criar_banco.sh

echo "Criando banco de dados FinGuia..."

SCHEMA_FILE="backend/app/db/schema.sql"

if [ ! -f "$SCHEMA_FILE" ]; then
    echo "Erro: Arquivo $SCHEMA_FILE não encontrado!"
    exit 1
fi

docker exec -i finguia-postgres psql -U finguia -d finguia_db < "$SCHEMA_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Banco de dados criado com sucesso!"
else
    echo "❌ Erro ao criar banco de dados"
    exit 1
fi

