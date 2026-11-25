import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import api from '../services/api'

type Item = { id: string; name: string; amount_cents: number; kind: 'income' | 'expense' | 'budget' | 'reserve'; payer: string; frequency: string; month: string; day?: string; months?: number }
type Overview = { month: string; actual: { income: number; expense: number; third: number; balance: number; pending: number }; planned: { income: number; expense: number; third: number; budget: number; reserve: number; available: number; cost_of_living: number }; items: Item[] }
const money = (cents: number) => (cents / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const label = (month: string) => new Date(month + '-01T12:00:00').toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })
const card = 'rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900'
const groups = [
  { title: 'Receitas previstas', test: (i: Item) => i.kind === 'income' && i.frequency !== 'actual' },
  { title: 'Despesas próprias previstas', test: (i: Item) => i.kind === 'expense' && i.payer === 'self' && i.frequency !== 'actual' },
  { title: 'Despesas previstas de terceiros', test: (i: Item) => i.kind === 'expense' && i.payer === 'third' && i.frequency !== 'actual' },
  { title: 'Despesas pagas por terceiros', test: (i: Item) => i.frequency === 'actual' && i.payer === 'third' },
  { title: 'Limites de orçamento', test: (i: Item) => i.kind === 'budget' },
  { title: 'Metas de reserva', test: (i: Item) => i.kind === 'reserve' },
]
export default function FinancialPlanning({ month, mode = 'all' }: { month: Date; mode?: 'all' | 'expenses' | 'reserve' }) {
  const key = format(month, 'yyyy-MM')
  const { data, isLoading, isError, refetch } = useQuery<Overview>({
    queryKey: ['financial-overview', key],
    queryFn: async () => (await api.get('/chatbot/overview', { params: { month: key } })).data,
  })
  if (isLoading) return <section className={card}>Carregando planejamento...</section>
  if (isError || !data) return <section className={card}><p>Não foi possível carregar o planejamento.</p><button onClick={() => refetch()} className="mt-2 underline">Tentar novamente</button></section>
  const p = data.planned
  const a = data.actual
  const visible = groups.filter((_, i) => mode === 'all' || (mode === 'expenses' && i >= 1 && i <= 3) || (mode === 'reserve' && i === 5))
  const metrics = mode === 'all' ? [
    ['Receita prevista', p.income], ['Despesas próprias previstas', p.expense], ['Despesas previstas de terceiros', p.third],
    ['Limite de orçamento', p.budget], ['Meta de reserva', p.reserve], ['Disponível planejado', p.available],
    ['Custo de vida previsto (inclui terceiros e limites)', p.cost_of_living],
    ['Resultado próprio realizado', a.balance], ['Receitas recebidas', a.income], ['Despesas próprias pagas', a.expense], ['Terceiros já pagos', a.third], ['Contas próprias em aberto', a.pending],
  ] as [string, number][] : []
  return <section className={card + ' space-y-4 text-slate-900 dark:text-slate-100'}>
    <div><h2 className="text-lg font-bold">Planejamento financeiro</h2><p className="text-sm text-slate-500 dark:text-slate-400 capitalize">{label(key)} · registros confirmados no chat</p></div>
    {mode === 'all' && <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{metrics.map(([name, amount]) => <div key={name} className="rounded-md border border-slate-200 p-3 dark:border-slate-700"><p className="text-xs text-slate-500 dark:text-slate-400">{name}</p><p className="mt-1 text-lg font-semibold tabular-nums break-words">{money(amount)}</p></div>)}</div>}
    <p className="text-xs text-slate-500 dark:text-slate-400">Previsões não são pagamentos. Gastos de terceiros e metas não são descontados do saldo realizado. O disponível planejado não é saldo bancário.</p>
    {visible.map(g => {
      const items = data.items.filter(g.test)
      if (!items.length) return null
      return <details key={g.title} className="rounded-md border border-slate-200 p-3 dark:border-slate-700"><summary className="cursor-pointer font-medium">{g.title} · {money(items.reduce((sum, i) => sum + i.amount_cents, 0))}</summary><div className="mt-3 space-y-2">{items.map(i => <div key={i.id} className="flex justify-between gap-3 border-t border-slate-200 pt-2 text-sm dark:border-slate-700"><div className="min-w-0"><p className="break-words">{i.name}</p><p className="text-xs text-slate-500">{i.frequency === 'monthly' ? 'Mensal' : i.frequency === 'actual' ? 'Realizado' : 'Pontual'}{i.frequency !== 'monthly' && i.day ? ' · ' + i.day.split('-').reverse().join('/') : ''}{i.months ? ' · ' + i.months + ' meses' : ''}</p></div><span className="shrink-0 font-medium">{money(i.amount_cents)}</span></div>)}</div></details>
    })}
    {!data.items.some(i => visible.some(g => g.test(i))) && <p className="text-sm text-slate-500">Nenhum item de planejamento para este mês. Cadastre e confirme pelo chat.</p>}
  </section>
}
