#!/bin/bash
# Script para zerar todos os usuários do banco de dados
# Uso: bash scripts/zerar_usuarios.sh

URL="https://economizeia-production.up.railway.app/api/v1/reset-all-users"

echo "⚠️  ATENÇÃO: Isso vai deletar TODOS os usuários do banco de dados!"
echo ""
read -p "Digite 'SIM' para confirmar: " confirm

if [ "$confirm" != "SIM" ]; then
    echo "Operação cancelada."
    exit 1
fi

echo ""
echo "Enviando requisição DELETE..."

response=$(curl -s -X DELETE "$URL" -H "Content-Type: application/json")

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Sucesso!"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
else
    echo ""
    echo "❌ Erro ao deletar usuários"
fi

