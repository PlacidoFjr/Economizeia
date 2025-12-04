# 📋 Plano de Melhorias Completas - FinGuia

## ✅ 1. Chatbot Mais Sucinto (FEITO)
- ✅ Prompt otimizado para respostas curtas
- ✅ Contexto reduzido (apenas dados essenciais)
- ✅ Economia de tokens

## ✅ 2. Sistema de Toast Notifications (FEITO)
- ✅ Componente Toast criado
- ✅ ToastContainer criado
- ⏳ Integrar no App.tsx
- ⏳ Usar em Login/Register para mensagens de erro

## 🔄 3. Separar Boletos de Finanças

### Backend:
- ⏳ Adicionar campo `is_bill` ao modelo Bill
- ⏳ Atualizar schema.sql
- ⏳ Criar migração
- ⏳ Atualizar endpoints para filtrar por `is_bill`
- ⏳ Endpoint DELETE para boletos/finanças

### Frontend:
- ⏳ Criar página `Finances.tsx` (não-boletos)
- ⏳ Atualizar `Bills.tsx` para mostrar apenas boletos
- ⏳ Adicionar botão deletar em ambas páginas
- ⏳ Atualizar navegação (Layout.tsx)
- ⏳ Atualizar rotas (App.tsx)
- ⏳ Atualizar Dashboard para separar
- ⏳ Atualizar AddExpense para definir `is_bill`

## 📝 Próximos Passos

1. Integrar Toast no App
2. Adicionar campo is_bill no schema
3. Criar migração
4. Criar página Finanças
5. Adicionar botão deletar
6. Atualizar todas as referências

