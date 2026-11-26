import MonthlySpending from '../components/MonthlySpending'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format, parseISO, startOfMonth } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { ArrowDownLeft, ArrowUpRight, CalendarDays, ChevronDown, Plus, WalletCards } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import FinancialPlanning, { financialMoney as money, useFinancialOverview } from '../components/FinancialPlanning'
import type { FinancialActivityRow } from '../components/FinancialPlanning'
import LoadingSpinner from '../components/LoadingSpinner'
import MonthSelector from '../components/MonthSelector'
import api from '../services/api'
import { translateCategory, translateStatus } from '../utils/translations'

type Investment = { amount_invested: number; current_value: number | null; type: string }

const panel = 'min-w-0 rounded-xl border border-slate-200 bg-white p-4 sm:p-5'
const muted = 'text-sm text-slate-500'
const heading = 'text-base font-semibold text-slate-950'
const link = 'text-sm font-semibold text-teal-800 underline-offset-4 hover:underline dark:text-teal-300'
const investmentsTypes: Record<string, string> = {
  stock: 'Ações', fixed_income: 'Renda fixa', fund: 'Fundos', crypto: 'Criptomoedas',
  real_estate: 'Imóveis', other: 'Outros',
}
const compactCurrency = new Intl.NumberFormat('pt-BR', { notation: 'compact', maximumFractionDigits: 1 })

function Rankings({ entries, category = false }: { entries: Record<string, number>; category?: boolean }) {
  const ordered = Object.entries(entries).sort((a, b) => b[1] - a[1])
  const total = ordered.reduce((sum, [, value]) => sum + value, 0)
  if (!ordered.length || total <= 0) return <p className={muted + ' py-5'}>Nenhuma despesa realizada neste mês.</p>
  return (
    <ul className="mt-4 space-y-3">
      {ordered.map(([name, value]) => (
        <li key={name}>
          <div className="flex flex-wrap justify-between gap-x-2 text-sm text-slate-950">
            <span className="min-w-0 break-words">{category ? translateCategory(name) : name}</span>
            <span className="font-semibold tabular-nums">{money(value)}</span>
          </div>
          <div className="mt-1.5 h-1.5 rounded-full bg-slate-100 dark:bg-slate-700" aria-hidden="true">
            <div className="h-full rounded-full bg-teal-600 dark:bg-teal-400" style={{ width: Math.max(0, Math.min(value / total * 100, 100)) + '%' }} />
          </div>
        </li>
      ))}
    </ul>
  )
}

function ActivityList({ items, empty, upcoming = false }: { items: FinancialActivityRow[]; empty: string; upcoming?: boolean }) {
  if (!items.length) return <p className={muted + ' py-5'}>{empty}</p>
  return (
    <ul className="mt-3 divide-y divide-slate-100 dark:divide-slate-700">
      {items.map((item) => (
        <li key={item.id} className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 py-3">
          <div className="min-w-0 flex-1">
            <p className="break-words text-sm font-semibold text-slate-950">{item.name}</p>
            <p className={muted}>
              {format(parseISO(item.day), 'dd/MM/yyyy')} · {item.status === 'planned' ? 'Previsto' : translateStatus(item.status)}
            </p>
          </div>
          <span className={'text-sm font-semibold tabular-nums ' + (item.type === 'income' ? 'text-teal-800 dark:text-teal-300' : 'text-slate-950')}>
            {!upcoming && (item.type === 'income' ? '+' : '−')}{money(item.amount_cents)}
          </span>
        </li>
      ))}
    </ul>
  )
}

function InvestmentSummary() {
  const { data, isError, refetch } = useQuery({
    queryKey: ['investments'],
    queryFn: async () => (await api.get<Investment[]>('/investments')).data,
  })
  if (isError && !data) return (
    <section className={panel}>
      <h2 className={heading}>Investimentos</h2>
      <p className={muted + ' mt-2'}>Não foi possível carregar a carteira.</p>
      <button className={link + ' mt-2'} onClick={() => refetch()}>Tentar novamente</button>
    </section>
  )
  if (!data?.length) return null
  const allocation: Record<string, number> = {}
  let invested = 0
  let current = 0
  for (const item of data) {
    const amount = Math.round(item.amount_invested * 100)
    const value = Math.round((item.current_value ?? item.amount_invested) * 100)
    const type = investmentsTypes[item.type] ?? investmentsTypes.other
    invested += amount
    current += value
    allocation[type] = (allocation[type] ?? 0) + value
  }
  const change = current - invested
  return (
    <section className={panel}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className={heading}>Carteira de investimentos</h2>
        <Link className={link} to="/app/investments">Ver investimentos</Link>
      </div>
      <dl className="mt-4 grid gap-4 sm:grid-cols-3">
        {[['Valor atual', current], ['Total investido', invested], ['Resultado', change]].map(([name, amount]) => (
          <div key={name}><dt className={muted}>{name}</dt><dd className="mt-1 font-semibold tabular-nums text-slate-950">{money(Number(amount))}</dd></div>
        ))}
      </dl>
      {Object.values(allocation).some((value) => value > 0) && (
        <details className="mt-4 border-t border-slate-200 pt-3">
          <summary className="cursor-pointer text-sm font-semibold text-slate-700">Distribuição da carteira</summary>
          <Rankings entries={allocation} />
        </details>
      )}
    </section>
  )
}

export default function Dashboard() {
  const [selectedMonth, setSelectedMonth] = useState(() => startOfMonth(new Date()))
  const { data, isLoading, isError, refetch } = useFinancialOverview(selectedMonth)
  const activity = data?.activity
  const trend = activity?.trend.map((item) => ({
    label: format(parseISO(item.month + '-01'), 'MMM', { locale: ptBR }),
    income: item.income,
    expense: item.expense,
  })) ?? []

  return (
    <div className="space-y-5 pb-20 text-slate-950 sm:pb-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Visão geral</h1>
        <div className="flex flex-wrap items-center gap-2">
          <MonthSelector value={selectedMonth} onChange={setSelectedMonth} compact />
          <Link to="/app/transactions/add" className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-teal-800 px-3 text-sm font-semibold text-white hover:bg-teal-900">
            <Plus size={16} aria-hidden="true" /> Novo lançamento
          </Link>
        </div>
      </header>

      {isLoading && <LoadingSpinner message="Carregando dados do painel..." />}
      {isError && !data && (
        <section className={panel} role="alert">
          <p>Não foi possível carregar o resumo deste mês.</p>
          <button className={link + ' mt-2'} onClick={() => refetch()}>Tentar novamente</button>
        </section>
      )}
      {data && (
        <>
          <section aria-label="Resumo do mês" className="grid overflow-hidden rounded-xl border border-slate-200 bg-white lg:grid-cols-[1.18fr_2fr]">
            <div className="bg-[#123b3a] p-5 text-white sm:p-6">
              <p className="flex items-center gap-2 text-sm font-medium text-teal-100"><WalletCards size={17} aria-hidden="true" /> Saldo realizado no mês</p>
              <p className="mt-3 break-words text-3xl font-bold tracking-tight tabular-nums sm:text-4xl">{money(data.actual.balance)}</p>
              <p className="mt-2 text-sm text-teal-100">Receitas recebidas menos despesas próprias</p>
            </div>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-4 p-5 md:grid-cols-3 sm:p-6">
              {[
                { label: 'Receitas realizadas', value: data.actual.income, icon: ArrowUpRight },
                { label: 'Despesas realizadas', value: data.actual.expense, icon: ArrowDownLeft },
                { label: 'Contas em aberto', value: data.actual.pending, icon: CalendarDays },
              ].map(({ label, value, icon: Icon }) => (
                <div key={label} className="min-w-0 last:col-span-full md:last:col-span-1">
                  <dt className="flex items-center gap-1.5 text-sm text-slate-600"><Icon size={16} className="shrink-0 text-teal-700 dark:text-teal-300" aria-hidden="true" /> {label}</dt>
                  <dd className="mt-2 break-words text-lg font-bold tabular-nums">{money(value)}</dd>
                </div>
              ))}
            </dl>
          </section>

          <MonthlySpending month={selectedMonth} />

          {activity && activity.overdue_count > 0 && (
            <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-100">
              <a href="#vencimentos" className="font-semibold underline underline-offset-4">
                {activity.overdue_count === 1 ? '1 conta vencida no mês' : activity.overdue_count + ' contas vencidas no mês'}
              </a>
            </div>
          )}

          {activity && (
            <>
              <div className="grid gap-4 lg:grid-cols-[1.55fr_1fr]">
                <section className={panel}>
                  <h2 className={heading}>Evolução financeira</h2>
                  <p className={muted + ' mt-1'}>Receitas e despesas realizadas em seis meses</p>
                  {trend.some(({ income, expense }) => income || expense) ? (
                    <div className="mt-4 h-64 min-w-0">
                      <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                        <BarChart data={trend} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
                          <CartesianGrid vertical={false} stroke="#94a3b8" strokeOpacity={0.25} />
                          <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={12} />
                          <YAxis width={46} tickLine={false} axisLine={false} fontSize={11} tickFormatter={(value) => compactCurrency.format(value / 100)} />
                          <Tooltip formatter={(value) => money(Number(value))} />
                          <Legend />
                          <Bar name="Receitas" dataKey="income" fill="#0f766e" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                          <Bar name="Despesas" dataKey="expense" fill="#b76840" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  ) : <p className={muted + ' py-5'}>Nenhuma movimentação realizada no período.</p>}
                </section>
                <section className={panel}>
                  <h2 className={heading}>Gastos por categoria</h2>
                  <Rankings entries={activity.categories} category />
                  {Object.keys(activity.issuers).length > 0 && (
                    <details className="mt-4 border-t border-slate-200 pt-3">
                      <summary className="cursor-pointer text-sm font-semibold text-slate-700">Ver maiores gastos por emissor</summary>
                      <Rankings entries={Object.fromEntries(Object.entries(activity.issuers).sort((a, b) => b[1] - a[1]).slice(0, 10))} />
                    </details>
                  )}
                </section>
              </div>
              <div className="grid gap-4 lg:grid-cols-2">
                <section id="vencimentos" tabIndex={-1} className={panel + ' scroll-mt-20'}>
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <h2 className={heading}>Vencimentos do mês{activity.open_count > 0 && ' (' + activity.open_count + ')'}</h2>
                    <Link to="/app/finances" className={link}>Ver finanças</Link>
                  </div>
                  <ActivityList items={activity.upcoming} empty="Nenhuma conta em aberto neste mês." upcoming />
                  {!!activity.planned_due?.length && (
                    <details className="mt-4 border-t border-slate-200 pt-3">
                      <summary className="cursor-pointer text-sm font-semibold text-slate-700">Compromissos previstos</summary>
                      <ActivityList items={activity.planned_due} empty="Nenhum compromisso previsto." upcoming />
                    </details>
                  )}
                </section>
                <section className={panel}>
                  <h2 className={heading}>Lançamentos do mês</h2>
                  <ActivityList items={activity.recent} empty="Nenhum lançamento neste mês." />
                </section>
              </div>
            </>
          )}

          <details className={panel + ' group'}>
            <summary className="flex cursor-pointer list-none items-center justify-between gap-3 rounded text-base font-semibold">
              Planejamento financeiro
              <ChevronDown size={19} className="shrink-0 text-slate-500 group-open:rotate-180" aria-hidden="true" />
            </summary>
            <div className="mt-4"><FinancialPlanning month={selectedMonth} /></div>
          </details>
        </>
      )}
      <InvestmentSummary />
    </div>
  )
}
