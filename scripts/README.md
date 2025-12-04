# Scripts Auxiliares

## seed_data.py

Script para popular o banco de dados com dados sintéticos para testes.

**Uso:**
```bash
cd backend
python scripts/seed_data.py
```

**Cria:**
- 1 usuário de teste (teste@finguia.com / senha123)
- 2 contas (Conta Corrente e Poupança)
- 20 boletos com diferentes status e confiança
- 10 pagamentos agendados/executados

## test_api.sh

Script de teste da API usando curl.

**Uso:**
```bash
chmod +x scripts/test_api.sh
./scripts/test_api.sh
```

**Requisitos:**
- `jq` instalado (para formatação JSON)
- API rodando em http://localhost:8000

