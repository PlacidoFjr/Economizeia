import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import api from '../services/api'
import { useFinancialOverview, financialMoney as money } from './FinancialPlanning'
import { translateCategory } from '../utils/translations'

export type SpendingTransaction = { id: string; name: string; day: string; amount_cents: number; category: string; plan_id: string | null; needs_link: boolean }
export type SpendingItem = { id: string; name: string; category: string; planned: number; actual: number; remaining: number; percent: number; transactions: SpendingTransaction[] }
export type SpendingCategory = { category: string; planned: number | null; actual: number; remaining: number | null; percent: number | null; basis: string; items: SpendingItem[]; transactions: SpendingTransaction[] }
const categories = ['transporte', 'alimentacao', 'moradia', 'saude', 'lazer', 'educacao', 'servicos', 'impostos', 'dividas', 'outras']
const labels: Record<string, string> = { lazer: 'Lazer', educacao: 'Educação', impostos: 'Impostos', dividas: 'Dívidas' }
const categoryName = (key: string) => labels[key] || translateCategory(key)
const input = 'min-h-10 rounded-md border border-slate-300 bg-white p-2 text-sm dark:border-slate-600 dark:bg-slate-900'

function Progress({ planned, actual }: { planned: number | null; actual: number }) {
  const percent = planned ? actual / planned * 100 : 0
  return <div className="mt-2">
    <div className="flex flex-wrap justify-between gap-2 text-sm">
      <span>Realizado <strong className="tabular-nums">{money(actual)}</strong></span>
      <span>{planned === null ? 'Sem previsão cadastrada' : 'Previsto ' + money(planned)}</span>
    </div>
    {planned !== null && <>
      <div role="progressbar" aria-label="Utilização do previsto" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.min(100, Math.round(percent))}
        aria-valuetext={percent.toFixed(1) + '% utilizado'} className="my-2 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
        <div className={'h-full rounded-full ' + (actual > planned ? 'bg-amber-600' : 'bg-teal-700')} style={{ width: Math.min(100, Math.max(0, percent)) + '%' }} />
      </div>
      <p className={'text-sm ' + (actual > planned ? 'text-amber-800 dark:text-amber-200' : 'text-slate-600')}>
        {actual > planned ? 'Excesso de ' + money(actual - planned) : 'Restam ' + money(planned - actual)} · {percent.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}% utilizado
      </p>
    </>}
  </div>
}

export default function MonthlySpending({ month }: { month: Date }) {
  const { data } = useFinancialOverview(month)
  const client = useQueryClient()
  const [editing, setEditing] = useState<SpendingTransaction | null>(null)
  const [selected, setSelected] = useState('')
  const [category, setCategory] = useState('outras')
  const [notice, setNotice] = useState('')
  const mutation = useMutation({
    mutationFn: () => api.put('/chatbot/spending/' + editing?.id, { category, plan_id: selected || null }),
    onSuccess: async () => {
      await Promise.all(['financial-overview', 'finances', 'bills'].map(key => client.invalidateQueries({ queryKey: [key] })))
      setEditing(null)
      setNotice('Referência do gasto atualizada.')
    },
  })
  const groups = data?.spending ?? []
  const options = groups.flatMap(group => group.items)
  if (!data) return null
  return <section className="rounded-xl border border-slate-200 bg-white p-4 text-slate-950 dark:border-slate-700 dark:bg-slate-900 sm:p-5">
    <h2 className="text-base font-semibold">Gastos do mês</h2>
    <p className="mt-1 text-sm text-slate-500">{format(month, 'MM/yyyy')} · Acompanhe os gastos em relação ao previsto.</p>
    {notice && <p className="mt-2 text-sm" role="status">{notice}</p>}
    {!groups.length && <p className="mt-3 text-sm text-slate-500">Cadastre uma previsão ou registre seu primeiro gasto.</p>}
    <div className="mt-3 grid min-w-0 gap-3 lg:grid-cols-2">
      {groups.map(group => <details key={group.category} className="min-w-0 rounded-lg border border-slate-200 p-3 dark:border-slate-700">
        <summary className="cursor-pointer"><span className="font-semibold">{categoryName(group.category)}</span>
          <Progress planned={group.planned} actual={group.actual} />
        </summary>
        {group.basis === 'budget' && <p className="mt-2 text-xs text-slate-500">O limite de orçamento é a referência desta categoria.</p>}
        {group.items.map(item => <div key={item.id} className="mt-3 border-t border-slate-200 pt-2">
          <h3 className="text-sm font-semibold">{item.name}</h3>
          <Progress planned={item.planned} actual={item.actual} />
        </div>)}
        <ul className="mt-3 divide-y divide-slate-200">
          {group.transactions.map(transaction => <li key={transaction.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
            <div className="min-w-0"><p className="break-words font-medium">{transaction.name} · {money(transaction.amount_cents)}</p>
              <p className="text-xs text-slate-500">{transaction.day?.split('-').reverse().join('/')} · {options.find(item => item.id === transaction.plan_id)?.name || (transaction.needs_link ? 'Escolha a referência deste gasto' : 'Sem previsão cadastrada')}</p>
            </div>
            <button type="button" disabled={mutation.isPending} className="min-h-10 rounded-md border border-slate-300 px-2 text-sm font-semibold"
              aria-label={'Corrigir referência de ' + transaction.name} onClick={() => {
                mutation.reset()
                setEditing(transaction)
                setCategory(transaction.category)
                setSelected(transaction.plan_id || '')
              }}>Corrigir</button>
          </li>)}
        </ul>
      </details>)}
    </div>
    {editing && <form className="mt-4 space-y-3 rounded-lg border border-teal-300 p-3" onSubmit={event => { event.preventDefault(); mutation.mutate() }}>
      <h3 className="font-semibold">Referência de {editing.name}</h3>
      <label className="block text-sm">Categoria
        <select className={input + ' mt-1 block w-full'} disabled={mutation.isPending} value={category} onChange={event => { setCategory(event.target.value); setSelected('') }}>
          {[...new Set([...categories, category])].map(value => <option key={value} value={value}>{categoryName(value)}</option>)}
        </select>
      </label>
      <label className="block text-sm">Planejamento de referência
        <select className={input + ' mt-1 block w-full'} disabled={mutation.isPending} value={selected} onChange={event => setSelected(event.target.value)}>
          <option value="">Associar automaticamente pela categoria e descrição</option>
          {options.filter(item => item.category === category).map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
      </label>
      {mutation.isError && <p role="alert" className="text-sm text-red-700">Não foi possível atualizar. Confira a referência e tente novamente.</p>}
      <div className="flex gap-2">
        <button disabled={mutation.isPending} className="min-h-10 rounded-md bg-teal-800 px-3 text-sm font-semibold text-white">Salvar referência</button>
        <button type="button" disabled={mutation.isPending} className={input} onClick={() => setEditing(null)}>Cancelar</button>
      </div>
    </form>}
  </section>
}

