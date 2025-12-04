"""
Script de treinamento e testes para o chatbot do FinGuia.
Execute este script para testar diferentes cenários e melhorar as respostas.
"""

import asyncio
import json
from app.services.ollama_service import ollama_service

# Casos de teste para o chatbot
TEST_CASES = [
    # Criação de despesas
    {
        "message": "Adicionar despesa de R$ 150,50 para energia elétrica",
        "expected_action": "create_expense",
        "description": "Criar despesa simples com valor e emissor"
    },
    {
        "message": "Criar boleto de R$ 300,00 vencendo em 15/12/2024",
        "expected_action": "create_expense",
        "description": "Criar despesa com data específica"
    },
    {
        "message": "Adicionar gasto de R$ 50,00 com alimentação vencendo amanhã",
        "expected_action": "create_expense",
        "description": "Criar despesa com categoria e data relativa"
    },
    {
        "message": "Parcela 1 de 3 de R$ 150,00 para loja X",
        "expected_action": "create_expense",
        "description": "Criar despesa parcelada"
    },
    {
        "message": "Registrar conta de R$ 200,00 da empresa Y para dia 20",
        "expected_action": "create_expense",
        "description": "Criar despesa com data do mês"
    },
    
    # Consultas
    {
        "message": "Quantos boletos eu tenho?",
        "expected_action": "chat",
        "description": "Consulta sobre quantidade de boletos"
    },
    {
        "message": "Quanto tenho pendente?",
        "expected_action": "chat",
        "description": "Consulta sobre valor pendente"
    },
    {
        "message": "Tenho boletos vencidos?",
        "expected_action": "chat",
        "description": "Consulta sobre boletos vencidos"
    },
    {
        "message": "Como funciona o upload de boletos?",
        "expected_action": "chat",
        "description": "Pergunta sobre funcionalidade"
    },
    {
        "message": "Como agendar um pagamento?",
        "expected_action": "chat",
        "description": "Pergunta sobre agendamento"
    },
    
    # Casos negativos (não devem criar despesa)
    {
        "message": "Olá, como você está?",
        "expected_action": "chat",
        "description": "Cumprimento simples"
    },
    {
        "message": "Obrigado pela ajuda",
        "expected_action": "chat",
        "description": "Agradecimento"
    },
    {
        "message": "Quero ver meus boletos",
        "expected_action": "chat",
        "description": "Consulta sem criar despesa"
    },
]

async def test_expense_extraction():
    """Testa a extração de informações de despesas."""
    print("=" * 60)
    print("TESTE DE EXTRAÇÃO DE DESPESAS")
    print("=" * 60)
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] {test_case['description']}")
        print(f"Mensagem: {test_case['message']}")
        
        try:
            result = await ollama_service.extract_expense_from_message(test_case['message'])
            
            if result:
                print(f"✅ Ação detectada: {result.get('action')}")
                print(f"   Valor: R$ {result.get('amount', 0):.2f}")
                print(f"   Emissor: {result.get('issuer', 'N/A')}")
                print(f"   Data: {result.get('due_date', 'N/A')}")
                print(f"   Categoria: {result.get('category', 'N/A')}")
                if result.get('is_installment'):
                    print(f"   Parcela: {result.get('installment_current')}/{result.get('installment_total')}")
            else:
                print(f"ℹ️  Nenhuma despesa detectada (ação: chat)")
            
            # Verificar se corresponde ao esperado
            if test_case['expected_action'] == "create_expense" and result:
                print("✅ RESULTADO CORRETO")
            elif test_case['expected_action'] == "chat" and not result:
                print("✅ RESULTADO CORRETO")
            else:
                print("⚠️  RESULTADO INESPERADO")
                
        except Exception as e:
            print(f"❌ ERRO: {str(e)}")
        
        print("-" * 60)

async def test_chat_responses():
    """Testa as respostas do chat."""
    print("\n" + "=" * 60)
    print("TESTE DE RESPOSTAS DO CHAT")
    print("=" * 60)
    
    context = {
        "total_bills": 10,
        "pending_bills": 5,
        "overdue_bills": 2,
        "total_pending": 1500.50,
    }
    
    chat_tests = [
        "Quantos boletos eu tenho?",
        "Quanto tenho pendente?",
        "Tenho boletos vencidos?",
        "Como funciona o sistema?",
        "Preciso de ajuda",
    ]
    
    for i, message in enumerate(chat_tests, 1):
        print(f"\n[{i}/{len(chat_tests)}] Pergunta: {message}")
        
        try:
            response = await ollama_service.chat(
                message=message,
                context=context,
                conversation_history=[]
            )
            print(f"Resposta: {response[:200]}...")
            print("✅ Resposta gerada com sucesso")
        except Exception as e:
            print(f"❌ ERRO: {str(e)}")
        
        print("-" * 60)

async def main():
    """Executa todos os testes."""
    print("\n🤖 INICIANDO TESTES DO CHATBOT FINGUIA\n")
    
    # Teste de extração
    await test_expense_extraction()
    
    # Teste de chat
    await test_chat_responses()
    
    print("\n" + "=" * 60)
    print("✅ TESTES CONCLUÍDOS")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

