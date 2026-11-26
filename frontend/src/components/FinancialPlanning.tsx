import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import api from '../services/api'
import type { SpendingCategory } from './MonthlySpending'
import FinancialPlanManager from './FinancialPlanManager'

type Item = { id: string; name: string; amount_cents: number; kind: 'income' | 'expense' | 'budget' | 'reserve'; payer: string; payer_name?: string; shared?: boolean; frequency: string; month: string; day?: string; months?: number; occurrence_count?: number }
export type FinancialActivityRow = { id: string; name: string; amount_cents: number; day: string; type: 'expense' | 'income'; status: string; category?: string }
type FinancialActivity = { categories: Record<string, number>; issuers: Record<string, number>; trend: { month: string; income: number; expense: number }[]; open_count: number; overdue_count: number; upcoming: FinancialActivityRow[]; planned_due?: FinancialActivityRow[]; recent: FinancialActivityRow[] }
type Overview = { spending?: SpendingCategory[]; month: string; actual: { income: number; expense: number; third: number; balance: number; pending: number }; planned: { income: number; expense: number; third: number; budget: number; reserve: number; available: number; cost_of_living: number }; items: Item[]; activity?: FinancialActivity }
export const financialMoney = (cents: number) => (cents / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const money = financialMoney
const label = (month: string) => new Date(month + '-01T12:00:00').toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })
const card = 'rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900'
const groups = [
  { title: 'Receitas previstas', test: (i: Item) => i.kind === 'income' && i.frequency !== 'actual' },
  { title: 'Despesas próprias previstas', test: (i: Item) => i.kind === 'expense' && i.payer === 'self' && i.frequency !== 'actual' },
  { title: 'Despesas previstas de terceiros', test: (i: Item) => i.kind === 'expense' && i.payer === 'third' && i.frequency !== 'actual' },
  { title: 'Despesas pagas por terceiros', test: (i: Item) => i.frequency === 'actual' && i.payer === 'third' },
  { title: 'Limites de orçamento', test: (i: Item) => i.kind === 'budget' },
  { title: 'Metas de reserva', test: (i: Item) => i.kind === 'reserve' },
  { title: 'Despesas compartilhadas previstas', test: (i: Item) => i.kind === 'expense' && i.payer === 'shared' && i.frequency !== 'actual' },
]
export function useFinancialOverview(month: Date) {
  const key = format(month, 'yyyy-MM')
  return useQuery<Overview>({
    queryKey: ['financial-overview', key],
    queryFn: async () => (await api.get('/chatbot/overview', { params: { month: key } })).data,
  })
}

const itemAmount = (item: Item) => item.amount_cents * (item.occurrence_count ?? 1)
const frequencies: Record<string, string> = { monthly: 'Mensal', weekly: 'Semanal', yearly: 'Anual', actual: 'Realizado', once: 'Pontual' }

export default function FinancialPlanning({ month, mode = 'all' }: { month: Date; mode?: 'all' | 'expenses' | 'reserve' }) {
  const { data, isLoading, isError, refetch } = useFinancialOverview(month)
  if (isLoading) return <section className={card}>Carregando planejamento...</section>
  if (isError || !data) return <section className={card}><p>Não foi possível carregar o planejamento.</p><button onClick={() => refetch()} className="mt-2 underline">Tentar novamente</button></section>
  const p = data.planned
  const a = data.actual
  const visible = groups.filter((_, i) => mode === 'all' || (mode === 'expenses' && ((i >= 1 && i <= 3) || i === 6)) || (mode === 'reserve' && i === 5))
  const metrics = mode === 'all' ? [
    ['Receita prevista', p.income], ['Despesas próprias previstas', p.expense], ['Despesas previstas de terceiros', p.third],
    ['Limite de orçamento', p.budget], ['Meta de reserva', p.reserve], ['Disponível planejado', p.available],
    ['Custo de vida previsto', p.cost_of_living],
    ['Resultado próprio realizado', a.balance], ['Receitas recebidas', a.income], ['Despesas próprias pagas', a.expense], ['Terceiros já pagos', a.third], ['Contas próprias em aberto', a.pending],
  ] as [string, number][] : []
  return <section className={card + ' space-y-4 text-slate-900 dark:text-slate-100'}>
    <div><h2 className="text-lg font-bold">{mode === 'reserve' ? 'Reservas planejadas' : 'Planejamento financeiro'}</h2><p className="text-sm text-slate-500 dark:text-slate-400 capitalize">{label(data.month)}</p></div>
    {mode === 'all' && <FinancialPlanManager />}
    {mode === 'all' && <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{metrics.map(([name, amount]) => <div key={name} className="rounded-md border border-slate-200 p-3 dark:border-slate-700"><p className="text-xs text-slate-500 dark:text-slate-400">{name}</p><p className="mt-1 text-lg font-semibold tabular-nums break-words">{money(amount)}</p></div>)}</div>}
    {mode === 'all' && <p className="text-xs text-slate-500 dark:text-slate-400">O disponível planejado considera receitas e despesas previstas, limites e reservas. Gastos de terceiros entram no custo de vida.</p>}
    {visible.map(g => {
      const items = data.items.filter(g.test)
      if (!items.length) return null
      return <details key={g.title} className="rounded-md border border-slate-200 p-3 dark:border-slate-700">
        <summary className="cursor-pointer font-medium">{g.title} · {money(items.reduce((sum, item) => sum + itemAmount(item), 0))}</summary>
        <div className="mt-3 space-y-2">{items.map(item => (
          <div key={item.id} className="flex justify-between gap-3 border-t border-slate-200 pt-2 text-sm dark:border-slate-700">
            <div className="min-w-0">
              <p className="break-words">{item.name}</p>
              <p className="text-xs text-slate-500">
                {frequencies[item.frequency]}
                {item.day && ' · ' + item.day.split('-').reverse().join('/')}
                {item.months && ' · ' + item.months + ' meses'}
                {item.payer_name && ' · ' + item.payer_name}
                {item.shared && ' · Parte de terceiros'}
              </p>
            </div>
            <span className="shrink-0 font-medium">{money(itemAmount(item))}</span>
          </div>
        ))}</div>
      </details>
    })}
    {!data.items.some(i => visible.some(g => g.test(i))) && <p className="text-sm text-slate-500">Nenhum item de planejamento para este mês. Cadastre e confirme pelo chat.</p>}
  </section>
}
