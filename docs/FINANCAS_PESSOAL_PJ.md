# EconomizeIA — finanças pessoais e PJ

## Funcionalidades

- Contextos separados: pessoal e empresa (PJ).
- Contas com saldo inicial e saldo calculado de movimentações vinculadas.
- Pagador: próprio usuário, família, empresa ou terceiros.
- Gastos pagos pela família não reduzem o saldo do usuário.
- Orçamentos por categoria e mês, previsões recorrentes e projeção de seis meses.
- Transferências entre contas sem duplicar receitas/despesas.
- Metas de economia e investimentos filtrados por contexto.

## Acesso

Página **Pessoal / PJ** no menu da aplicação, rota /app/finance-workspace.

## Compatibilidade

Histórico preexistente permanece no contexto pessoal, pago pelo usuário por padrão. Nenhum dado pessoal do proprietário é publicado no repositório. O contrato PJ e as despesas devem ser cadastrados pela aplicação autenticada, não via scripts de seed.

## Publicação segura

1. Faça backup do PostgreSQL.
2. Teste em banco de homologação e aplique o SQL de backend/scripts/migrate_finance_scopes.sql.
3. Publique backend/frontend de uma versão compatível (backend inclui migração aditiva de colunas na inicialização).
4. Execute python -m compileall backend/app; no frontend use npm ci && npm run build.
5. Valide login, lançamento, despesa paga pela família, previsão, realização, transferência e metas.
6. Só promova para produção depois de validar os testes e o banco.

## Regras de contabilização

Previsões e limites de orçamento não entram no saldo realizado. Transferências entre contas alteram saldos, mas não são receita nova. Reserva registrada como meta não significa que o dinheiro foi depositado. O saldo da conta é estimado, não conciliado com extrato bancário.

Marcar uma previsão como realizada cria um lançamento sem conta vinculada. Para usar uma conta no fluxo atual, faça o lançamento realizado diretamente e cancele a previsão correspondente, evitando dupla contagem.

## Melhorias futuras

- Conciliação de saldo com extratos e datas efetivas de pagamentos/recebimentos.
- Parcelamentos com identificador específico, e não agrupados por emissor.
- Valores em Decimal/centavos inteiros em vez de float.
- Testes de integração com PostgreSQL e integração completa dos módulos legados.
