# 📧 Exemplo Visual: Como Funciona o Envio de Email

## 🎯 Resposta Rápida

**SIM!** Seu Gmail (`placidojunior34@gmail.com`) vai enviar emails para **QUALQUER** usuário que pedir redefinição de senha.

Mas os emails vão para os **endereços dos usuários**, não para o seu Gmail!

---

## 📨 Exemplo Prático

### Situação:
- Você configurou: `SMTP_USER=placidojunior34@gmail.com`
- Usuário do sistema: `maria@empresa.com` solicita redefinição

### O que acontece:

```
1. Maria acessa: http://localhost:3000/forgot-password
2. Digita: maria@empresa.com
3. Clica em "Enviar Link"

┌─────────────────────────────────────────┐
│  BACKEND PROCESSA:                       │
│  - Gera token de redefinição             │
│  - Prepara email com link                │
│  - Chama: send_email(                    │
│      to="maria@empresa.com",  ← DESTINO │
│      from="noreply@finguia.com"          │
│    )                                     │
└─────────────────────────────────────────┘
              │
              │ Conecta via SMTP
              ▼
┌─────────────────────────────────────────┐
│  SEU GMAIL (placidojunior34@gmail.com) │
│  - Autentica com sua senha de app       │
│  - RECEBE comando: "Envie email para   │
│    maria@empresa.com"                   │
│  - ENVIA o email                        │
└─────────────────────────────────────────┘
              │
              │ Email enviado
              ▼
┌─────────────────────────────────────────┐
│  CAIXA DE ENTRADA DA MARIA              │
│  maria@empresa.com                      │
│  📧 Recebe email de redefinição ✅      │
└─────────────────────────────────────────┘
```

---

## 🔄 Múltiplos Usuários

```
Usuário 1 (joao@exemplo.com) solicita
  → Seu Gmail envia → joao@exemplo.com recebe ✅

Usuário 2 (ana@teste.com) solicita
  → Seu Gmail envia → ana@teste.com recebe ✅

Usuário 3 (pedro@outro.com) solicita
  → Seu Gmail envia → pedro@outro.com recebe ✅
```

**Seu Gmail é o "carteiro" que entrega os emails!**

---

## ⚠️ Importante: Campo "From"

No código, linha 34:
```python
msg['From'] = self.smtp_from  # ← Este é o remetente que aparece
msg['To'] = to                 # ← Este é o destinatário (usuário)
```

No seu `.env`:
```env
SMTP_FROM=noreply@finguia.com  # ← Aparece como remetente
```

**Problema:** Gmail pode rejeitar se você tentar enviar "de" um email que não é seu.

**Solução:** Use seu próprio email:
```env
SMTP_FROM=placidojunior34@gmail.com
```

Ou com nome amigável:
```env
SMTP_FROM=FinGuia <placidojunior34@gmail.com>
```

---

## 📊 Fluxo Completo

```
┌─────────────────────────────────────────────────────────────┐
│  USUÁRIO DO SISTEMA                                          │
│  Email: joao@exemplo.com                                     │
│  Ação: Solicita redefinição de senha                         │
└─────────────────────────────────────────────────────────────┘
                        │
                        │ POST /api/v1/auth/forgot-password
                        │ { "email": "joao@exemplo.com" }
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  BACKEND FINGUIA                                             │
│  1. Busca usuário no banco                                   │
│  2. Gera token JWT (válido por 1 hora)                      │
│  3. Salva token no banco                                     │
│  4. Prepara email:                                           │
│     - To: joao@exemplo.com                                   │
│     - From: noreply@finguia.com                              │
│     - Subject: Redefinição de Senha                          │
│     - Body: Link com token                                   │
│  5. Chama: notification_service.send_email(...)             │
└─────────────────────────────────────────────────────────────┘
                        │
                        │ SMTP Connection
                        │ smtp.gmail.com:587
                        │ Login: placidojunior34@gmail.com
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  GMAIL SMTP SERVER                                           │
│  - Autentica: placidojunior34@gmail.com                     │
│  - Valida: Senha de app                                      │
│  - Aceita: Comando de envio                                 │
│  - Processa: Email para joao@exemplo.com                     │
└─────────────────────────────────────────────────────────────┘
                        │
                        │ Email Delivery
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  SERVIDOR DE EMAIL DO JOÃO                                  │
│  (exemplo.com)                                               │
│  - Recebe email                                              │
│  - Entrega na caixa de entrada                               │
└─────────────────────────────────────────────────────────────┘
                        │
                        │ Email Recebido
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  CAIXA DE ENTRADA DO JOÃO                                    │
│  joao@exemplo.com                                            │
│  📧 "Redefinição de Senha - FinGuia"                        │
│  📎 Link: .../reset-password?token=...                       │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Resumo

| Item | Valor |
|------|-------|
| **Quem envia?** | Seu Gmail (`placidojunior34@gmail.com`) |
| **Como autentica?** | Senha de app do Gmail |
| **Para quem vai?** | Email do usuário que solicitou |
| **Exemplo:** | `maria@empresa.com` solicita → recebe em `maria@empresa.com` |
| **Limite:** | ~500 emails/dia (Gmail pessoal) |

---

## 🎯 Analogia Simples

**Seu Gmail é como um "carteiro":**
- Você tem uma "licença" (senha de app) para usar o serviço postal do Gmail
- Quando alguém precisa receber uma carta (email), você usa o serviço postal
- A carta vai para o endereço do destinatário, não para sua casa
- Você é apenas o intermediário que usa o serviço

---

**Agora ficou claro?** Seu Gmail é o "servidor de envio", mas os emails vão para os usuários do sistema! 📧✅

