"""Script para testar o tamanho do contexto do chatbot"""
import json

# Simular contexto completo
context = {
    "user_name": "João",
    "total_bills": 50,
    "pending_bills": 20,
    "confirmed_bills": 15,
    "scheduled_bills": 5,
    "paid_bills": 10,
    "overdue_bills": 3,
    "total_pending": 5000.00,
    "total_paid": 3000.00,
    "monthly_expenses": 2500.00,
    "monthly_income": 3000.00,
    "monthly_balance": 500.00,
    "current_month": "12/2024",
    "categories": {
        "moradia": {"total": 1500.00, "count": 2, "bills": [{"issuer": "Aluguel", "amount": 1200.00}, {"issuer": "Condomínio", "amount": 300.00}]},
        "alimentacao": {"total": 800.00, "count": 5, "bills": [{"issuer": "Supermercado", "amount": 200.00}]},
        "servicos": {"total": 200.00, "count": 3, "bills": [{"issuer": "Internet", "amount": 89.90}]},
    },
    "top_issuers": {
        "Energia Elétrica": {"total": 300.00, "count": 2, "bills": [{"amount": 150.00}]},
        "Supermercado": {"total": 400.00, "count": 4, "bills": [{"amount": 100.00}]},
    },
    "next_bills": [
        {"issuer": "Aluguel", "amount": 1200.00, "due_date": "2024-12-10", "days_until": 5, "category": "moradia"},
        {"issuer": "Energia", "amount": 150.00, "due_date": "2024-12-15", "days_until": 10, "category": "servicos"},
    ],
    "overdue_details": [
        {"issuer": "Internet", "amount": 89.90, "due_date": "2024-11-30", "days_overdue": 5},
    ]
}

# Construir contexto como no código
context_text = f"""=== DADOS FINANCEIROS DO USUÁRIO ===

📊 RESUMO GERAL:
- Total de boletos cadastrados: {context.get('total_bills', 0)}
- Boletos pendentes: {context.get('pending_bills', 0)}
- Boletos confirmados: {context.get('confirmed_bills', 0)}
- Boletos agendados: {context.get('scheduled_bills', 0)}
- Boletos pagos: {context.get('paid_bills', 0)}
- Boletos vencidos: {context.get('overdue_bills', 0)}

💰 VALORES:
- Total pendente: R$ {context.get('total_pending', 0):.2f}
- Total pago: R$ {context.get('total_paid', 0):.2f}
- Despesas do mês ({context.get('current_month', 'atual')}): R$ {context.get('monthly_expenses', 0):.2f}
- Receitas do mês ({context.get('current_month', 'atual')}): R$ {context.get('monthly_income', 0):.2f}
- Saldo do mês: R$ {context.get('monthly_balance', 0):.2f} {'(positivo)' if context.get('monthly_balance', 0) >= 0 else '(negativo)'}

"""

if context.get('overdue_bills', 0) > 0:
    context_text += f"⚠️ BOLETOS VENCIDOS ({context.get('overdue_bills', 0)}):\n"
    for bill in context.get('overdue_details', [])[:5]:
        context_text += f"  - {bill.get('issuer', 'Desconhecido')}: R$ {bill.get('amount', 0):.2f} (vencido há {bill.get('days_overdue', 0)} dias)\n"
    context_text += "\n"

if context.get('next_bills'):
    context_text += f"📅 PRÓXIMOS BOLETOS A VENCER:\n"
    for bill in context.get('next_bills', [])[:5]:
        days = bill.get('days_until', 0)
        context_text += f"  - {bill.get('issuer', 'Desconhecido')}: R$ {bill.get('amount', 0):.2f} (vence em {days} dias) - {bill.get('category', 'sem categoria')}\n"
    context_text += "\n"

if context.get('categories'):
    context_text += f"🏷️ GASTOS POR CATEGORIA:\n"
    sorted_cats = sorted(context.get('categories', {}).items(), key=lambda x: x[1].get('total', 0), reverse=True)
    for cat, data in sorted_cats[:5]:
        context_text += f"  - {cat}: R$ {data.get('total', 0):.2f} ({data.get('count', 0)} boletos)\n"
    context_text += "\n"

if context.get('top_issuers'):
    context_text += f"🏢 TOP EMISSORES:\n"
    for issuer, data in list(context.get('top_issuers', {}).items())[:5]:
        context_text += f"  - {issuer}: R$ {data.get('total', 0):.2f} ({data.get('count', 0)} boletos)\n"
    context_text += "\n"

system_prompt = """Você é o assistente financeiro inteligente do FinGuia..."""  # (resumido)

user_prompt = f"""{context_text}

=== PERGUNTA ATUAL ===
Usuário: Quantos boletos eu tenho?

Assistente:"""

# Calcular tamanho
total_chars = len(system_prompt) + len(user_prompt)
estimated_tokens = total_chars / 4  # Aproximação: 1 token ≈ 4 caracteres

print(f"Tamanho do contexto:")
print(f"- Caracteres: {total_chars:,}")
print(f"- Tokens estimados: {estimated_tokens:.0f}")
print(f"- Limite configurado (num_ctx): 4096")
print(f"\n{'⚠️ CONTEXTO MUITO GRANDE!' if estimated_tokens > 3000 else '✅ Contexto OK'}")
print(f"\nContexto gerado ({len(context_text)} chars):")
print(context_text[:500] + "...")

