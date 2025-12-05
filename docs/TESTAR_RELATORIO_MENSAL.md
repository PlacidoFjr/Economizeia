# 📊 Como Testar o Relatório Mensal

## 🚀 Opção 1: Testar via API (Recomendado)

### Pré-requisitos
- Backend rodando (local ou Railway)
- Usuário cadastrado e email verificado
- Token JWT válido

### Passo a Passo

#### 1. Via Swagger UI (Mais Fácil)

1. Acesse: `http://localhost:8000/api/docs` (local) ou `https://seu-backend.railway.app/api/docs` (Railway)

2. Faça login primeiro:
   - Vá em **Autenticação** → `POST /api/v1/auth/login`
   - Clique em **"Try it out"**
   - Preencha email e senha
   - Clique em **"Execute"**
   - Copie o `access_token` da resposta

3. Autorize no Swagger:
   - Clique no botão **"Authorize"** (cadeado no topo)
   - Cole o token: `Bearer SEU_TOKEN_AQUI`
   - Clique em **"Authorize"**

4. Teste o relatório:
   - Vá em **Notificações** → `POST /api/v1/notifications/test-monthly-report`
   - Clique em **"Try it out"**
   - Opcional: ajuste `report_month` e `report_year`
   - Clique em **"Execute"**
   - ✅ O relatório será enviado para o email do usuário logado!

#### 2. Via cURL

```bash
# 1. Fazer login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "seu-email@exemplo.com",
    "password": "sua-senha"
  }'

# 2. Copiar o access_token da resposta e usar no próximo comando
curl -X POST "http://localhost:8000/api/v1/notifications/test-monthly-report" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "report_month": 11,
    "report_year": 2024
  }'
```

#### 3. Via Script Python

```bash
# Instale requests primeiro (se não tiver)
pip install requests

# Execute o script
python backend/scripts/test_monthly_report_http.py seu-email@exemplo.com sua-senha
```

---

## 🐳 Opção 2: Iniciar Backend Localmente

### Com Docker Compose

```bash
# Na raiz do projeto
docker-compose up -d

# Aguarde alguns segundos para os serviços iniciarem
# Verifique os logs
docker-compose logs -f backend
```

### Sem Docker (Desenvolvimento)

```bash
cd backend

# Ative o ambiente virtual
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente (.env)
# Inicie o servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## ✅ Verificar se Funcionou

1. **Confira os logs do backend:**
   ```
   ✅ Email sent successfully via Brevo to seu-email@exemplo.com
   ```

2. **Verifique sua caixa de entrada:**
   - Email: `seu-email@exemplo.com`
   - Assunto: `📊 Seu Relatório Financeiro de [Mês]/[Ano] - EconomizeIA`
   - **Importante:** Verifique também a pasta de **SPAM**

3. **O email deve conter:**
   - ✅ Saldo do mês (superávit/déficit)
   - ✅ Receitas vs Despesas
   - ✅ Status dos boletos
   - ✅ Top categorias de gastos
   - ✅ Metas de economia
   - ✅ Insights personalizados
   - ✅ Design responsivo e bonito

---

## 🔧 Troubleshooting

### Backend não responde
- Verifique se está rodando: `docker-compose ps`
- Veja os logs: `docker-compose logs backend`
- Verifique a porta: `netstat -an | findstr 8000` (Windows)

### Email não chega
- Verifique configuração do Brevo/SMTP no `.env` ou Railway
- Veja os logs do backend para erros de envio
- Verifique pasta de spam
- Confirme que o email está verificado no sistema

### Erro 401 (Não autorizado)
- Token expirado: faça login novamente
- Token inválido: verifique se copiou corretamente
- Usuário não autenticado: faça login primeiro

### Erro 500 (Erro interno)
- Verifique logs do backend
- Confirme que o banco de dados está conectado
- Verifique configurações de email (Brevo/SMTP)

---

## 📝 Dados de Teste Incluídos

O relatório de teste inclui dados fictícios:

- **Receitas:** R$ 5.000,00
- **Despesas:** R$ 4.200,00
- **Saldo:** R$ 800,00 (superávit)
- **Boletos:** 8 pagos, 2 pendentes, 0 vencidos
- **Top 5 categorias:** Alimentação, Transporte, Moradia, Lazer, Saúde
- **Metas:** Reserva de Emergência (25%) e Férias (26.7%)
- **Comparação:** +5.2% receitas, -3.1% despesas vs mês anterior

---

## 🎯 Próximos Passos

Após testar com sucesso:

1. ✅ O relatório será enviado **automaticamente** no dia 1 de cada mês
2. ✅ Configurado via Celery Beat no `celery_app.py`
3. ✅ Usa dados reais do banco de dados
4. ✅ Enviado para todos os usuários ativos e verificados

---

## 📞 Suporte

Se tiver problemas:
- Verifique os logs: `docker-compose logs backend`
- Confira as configurações no Railway (se em produção)
- Veja a documentação da API: `/api/docs`

