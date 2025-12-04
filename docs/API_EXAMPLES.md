# Exemplos de Uso da API FinGuia

## Autenticação

### 1. Registrar Usuário

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "João Silva",
    "email": "joao@example.com",
    "password": "senha123",
    "phone": "+5511999999999"
  }'
```

**Resposta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "joao@example.com",
    "password": "senha123"
  }'
```

### 3. Refresh Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

## Boletos

### 4. Upload de Boleto

```bash
curl -X POST http://localhost:8000/api/v1/bills/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/boleto.pdf"
```

**Resposta:**
```json
{
  "bill_id": "550e8400-e29b-41d4-a716-446655440000",
  "preview": {
    "issuer": null,
    "amount": null,
    "currency": "BRL",
    "due_date": null,
    "barcode": null,
    "confidence": 0.0,
    "requires_manual_review": true
  },
  "requires_manual_review": true
}
```

### 5. Obter Detalhes do Boleto

```bash
curl -X GET http://localhost:8000/api/v1/bills/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Resposta:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "issuer": "Energia Elétrica",
  "amount": 150.50,
  "currency": "BRL",
  "due_date": "2025-12-20",
  "barcode": "34191.09008 01234.567890 12345.678901 2 12345678901",
  "status": "pending",
  "confidence": 0.85,
  "category": "servicos",
  "ocr_text": "...",
  "extracted_json": {
    "issuer": "Energia Elétrica",
    "amount": 150.50,
    "due_date": "2025-12-20",
    "confidence": 0.85
  }
}
```

### 6. Confirmar Boleto

```bash
curl -X POST http://localhost:8000/api/v1/bills/550e8400-e29b-41d4-a716-446655440000/confirm \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "confirm": true,
    "corrections": {
      "issuer": "Energia Elétrica - Correção",
      "amount": 150.75
    }
  }'
```

### 7. Agendar Pagamento

```bash
curl -X POST http://localhost:8000/api/v1/bills/550e8400-e29b-41d4-a716-446655440000/schedule \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scheduled_date": "2025-12-18",
    "method": "PIX",
    "notify_before_days": [7, 3, 1]
  }'
```

### 8. Marcar como Pago

```bash
curl -X POST http://localhost:8000/api/v1/bills/550e8400-e29b-41d4-a716-446655440000/mark-paid \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "executed_date=2025-12-18" \
  -F "comprovante=@/path/to/comprovante.pdf"
```

### 9. Listar Boletos

```bash
curl -X GET "http://localhost:8000/api/v1/bills?from=2025-12-01&to=2025-12-31&status=pending" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Pagamentos

### 10. Listar Pagamentos

```bash
curl -X GET http://localhost:8000/api/v1/payments \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 11. Reconciliar Pagamento

```bash
curl -X POST http://localhost:8000/api/v1/payments/660e8400-e29b-41d4-a716-446655440000/reconcile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Notificações

### 12. Testar Notificação

```bash
curl -X POST http://localhost:8000/api/v1/notifications/test \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "reminder",
    "channel": "email"
  }'
```

### 13. Logs de Notificações

```bash
curl -X GET http://localhost:8000/api/v1/notifications/logs \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## QA

### 14. Itens Pendentes de Revisão

```bash
curl -X GET http://localhost:8000/api/v1/qa/pending \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 15. Resolver Item de QA

```bash
curl -X POST http://localhost:8000/api/v1/qa/550e8400-e29b-41d4-a716-446655440000/resolve \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resolution": {
      "issuer": "Energia Elétrica",
      "amount": 150.50,
      "due_date": "2025-12-20"
    }
  }'
```

## Códigos de Status HTTP

- `200 OK`: Sucesso
- `201 Created`: Recurso criado
- `400 Bad Request`: Requisição inválida
- `401 Unauthorized`: Não autenticado
- `403 Forbidden`: Sem permissão
- `404 Not Found`: Recurso não encontrado
- `500 Internal Server Error`: Erro do servidor

## Tratamento de Erros

Todas as respostas de erro seguem o formato:

```json
{
  "detail": "Mensagem de erro descritiva"
}
```

## Rate Limiting

- **Limite**: 100 requisições por minuto por IP
- **Header de resposta**: `X-RateLimit-Remaining`
- **Status**: `429 Too Many Requests` quando excedido

