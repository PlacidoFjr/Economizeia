#!/bin/bash
# Script de teste da API com curl

BASE_URL="http://localhost:8000/api/v1"

echo "=== Testando API FinGuia ==="

# 1. Registrar usuário
echo -e "\n1. Registrando usuário..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "test123"
  }')

echo "$REGISTER_RESPONSE" | jq '.'

ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.access_token')

if [ "$ACCESS_TOKEN" == "null" ]; then
  echo "Erro ao registrar. Tentando login..."
  LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "test@example.com",
      "password": "test123"
    }')
  ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
fi

echo "Token: ${ACCESS_TOKEN:0:20}..."

# 2. Listar boletos
echo -e "\n2. Listando boletos..."
curl -s -X GET "$BASE_URL/bills" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'

# 3. Listar pagamentos
echo -e "\n3. Listando pagamentos..."
curl -s -X GET "$BASE_URL/payments" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'

# 4. Listar notificações
echo -e "\n4. Listando logs de notificações..."
curl -s -X GET "$BASE_URL/notifications/logs" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'

# 5. QA - Itens pendentes
echo -e "\n5. Itens pendentes de QA..."
curl -s -X GET "$BASE_URL/qa/pending" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'

echo -e "\n=== Testes concluídos ==="

