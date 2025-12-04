# 🤖 Guia de Testes do Chatbot FinGuia

## ✅ Melhorias Implementadas

### 1. **Prompt do Sistema Aprimorado**
- ✅ Informações completas sobre todas as funcionalidades
- ✅ Exemplos de comandos e respostas
- ✅ Contexto rico sobre o sistema FinGuia
- ✅ Regras claras de comportamento

### 2. **Extração de Despesas Melhorada**
- ✅ Suporta múltiplos formatos de valores (R$ 150,50, 150.50, etc.)
- ✅ Reconhece datas em vários formatos (15/12/2024, amanhã, dia 20, etc.)
- ✅ Categorização inteligente por palavras-chave
- ✅ Detecção de parcelas
- ✅ Extração de emissor/fornecedor

### 3. **Contexto Financeiro Rico**
- ✅ Total de boletos por status
- ✅ Valores pendentes e pagos
- ✅ Gastos por categoria
- ✅ Top emissores
- ✅ Informações detalhadas para respostas personalizadas

### 4. **Perguntas Rápidas Atualizadas**
- ✅ "Quantos boletos eu tenho?"
- ✅ "Quanto tenho pendente?"
- ✅ "Como adicionar uma despesa?"
- ✅ "Ver meus boletos vencidos"

---

## 🧪 Como Testar o Chatbot

### Teste 1: Criar Despesas

Teste estes comandos no chatbot:

1. **Despesa Simples:**
   ```
   Adicionar despesa de R$ 150,50 para energia elétrica
   ```

2. **Despesa com Data:**
   ```
   Criar boleto de R$ 300,00 vencendo em 15/12/2024
   ```

3. **Despesa com Categoria:**
   ```
   Adicionar gasto de R$ 50,00 com alimentação vencendo amanhã
   ```

4. **Despesa Parcelada:**
   ```
   Parcela 1 de 3 de R$ 150,00 para loja X
   ```

5. **Despesa com Data Relativa:**
   ```
   Registrar conta de R$ 200,00 da empresa Y para dia 20
   ```

### Teste 2: Consultas

1. **Quantidade de Boletos:**
   ```
   Quantos boletos eu tenho?
   ```

2. **Valor Pendente:**
   ```
   Quanto tenho pendente?
   ```

3. **Boletos Vencidos:**
   ```
   Tenho boletos vencidos?
   ```

4. **Funcionalidades:**
   ```
   Como funciona o upload de boletos?
   Como agendar um pagamento?
   O que é o FinGuia?
   ```

### Teste 3: Dicas e Ajuda

1. **Dicas Financeiras:**
   ```
   Me dê dicas de economia
   Como organizar minhas finanças?
   ```

2. **Ajuda Geral:**
   ```
   Preciso de ajuda
   O que você pode fazer?
   ```

---

## 🔧 Executar Testes Automatizados

Para executar os testes automatizados:

```powershell
cd backend
python -m app.services.chatbot_training
```

Ou via Docker:

```powershell
docker exec finguia-backend python -m app.services.chatbot_training
```

---

## 📊 O que o Chatbot Pode Fazer Agora

### ✅ Criar Despesas
- Extrai valor, emissor, data, categoria automaticamente
- Suporta parcelas
- Valida dados antes de criar

### ✅ Responder Consultas
- Quantidade de boletos
- Valores pendentes
- Boletos vencidos
- Estatísticas financeiras

### ✅ Explicar Funcionalidades
- Como fazer upload
- Como agendar pagamentos
- Como usar o dashboard
- Como gerenciar parcelados

### ✅ Dar Dicas
- Organização financeira
- Economia
- Planejamento

### ✅ Usar Contexto do Usuário
- Menciona números reais
- Personaliza respostas
- Sugere ações baseadas na situação

---

## 🎯 Próximos Passos

1. **Teste o chatbot** acessando http://localhost:3000
2. **Experimente diferentes comandos** e veja as respostas
3. **Reporte problemas** ou sugestões de melhoria
4. **Use o chatbot** para criar despesas e consultar informações

---

## 💡 Dicas de Uso

- Seja específico ao criar despesas: mencione valor, descrição e data
- Use perguntas claras para obter respostas melhores
- O chatbot aprende com o contexto, então quanto mais você usar, melhor fica
- Experimente diferentes formas de dizer a mesma coisa

---

**O chatbot está completamente treinado e pronto para uso! 🚀**

