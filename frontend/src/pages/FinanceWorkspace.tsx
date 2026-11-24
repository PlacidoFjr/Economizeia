import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { ArrowLeftRight, Briefcase, CalendarDays, PiggyBank, Plus, Wallet } from 'lucide-react'
import LoadingSpinner from '../components/LoadingSpinner'

type Scope = 'personal' | 'business'
type MoneyType = 'income' | 'expense'
type Payer = 'self' | 'family' | 'business' | 'other'
interface Account {
  id: string
  name: string
  scope: Scope
  type: string
  opening_balance: number
  calculated_balance: number
}
interface Overview {
  income: number
  expenses: number
  balance: number
  third_party_expenses: number
  planned_income: number
  planned_expenses: number
  planned_third_party: number
  budgets: { category: string; limit: number; spent: number; remaining: number }[]
}
interface Plan {
  id: string
  scope: Scope
  title: string
  type: MoneyType
  amount: number
  planned_date: string
  paid_by: Payer
  status: string
  category: string | null
}
interface Projection {
  month: string
  income: number
  expenses: number
  future_income: number
  future_expenses: number
  projected_net: number
}
const money = (n: number) => (n || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const today = () => { const now = new Date(); return [now.getFullYear(), String(now.getMonth() + 1).padStart(2, '0'), String(now.getDate()).padStart(2, '0')].join('-') }
const currentMonth = () => today().slice(0, 7)
const categories = [
  ['alimentacao','Alimentação'], ['moradia','Moradia'], ['transporte','Transporte'],
  ['saude','Saúde'], ['servicos','Serviços'], ['lazer','Lazer'],
  ['tributos','Tributos'], ['ferramentas','Ferramentas'], ['outras','Outras']
]
const inputClass = 'w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-400'
const section = 'rounded-xl border border-gray-200 bg-white p-4 sm:p-5 shadow-sm'
const btn = 'rounded-lg bg-gray-900 px-4 py-2 text-sm font-semibold text-white hover:bg-gray-800 disabled:opacity-50'
const smallBtn = 'rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50'
function Label({ children }: { children: React.ReactNode }) { return <label className="mb-1 block text-xs font-semibold text-gray-700">{children}</label> }
function Stat({ title, amount, foot }: { title: string; amount: number; foot?: string }) {
  return <div className={section}>
    <p className="text-xs text-gray-500">{title}</p>
    <p className="mt-1 text-xl font-bold text-gray-900">{money(amount)}</p>
    {foot && <p className="mt-1 text-xs text-gray-500">{foot}</p>}
  </div>
}

export default function FinanceWorkspace() {
  const qc = useQueryClient()
  const [scope, setScope] = useState<Scope>('personal')
  const [month, setMonth] = useState(currentMonth())
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [accountName, setAccountName] = useState('')
  const [openingBalance, setOpeningBalance] = useState('0')
  const [budgetCategory, setBudgetCategory] = useState('lazer')
  const [budgetAmount, setBudgetAmount] = useState('200')
  const [movement, setMovement] = useState({
    title: '', amount: '', type: 'expense' as MoneyType, category: 'outras',
    date: today(), paid_by: 'self' as Payer, account_id: '', status: 'planned',
    months: '1',
  })
  const [transfer, setTransfer] = useState({ from_account_id: '', to_account_id: '', amount: '', transferred_on: today() })

  const selectedMonth = month + '-01'
  const refresh = () => {
    qc.invalidateQueries({ queryKey: ['finance-workspace'] })
    qc.invalidateQueries({ queryKey: ['bills'] })
    qc.invalidateQueries({ queryKey: ['finances'] })
    qc.invalidateQueries({ queryKey: ['dashboard'] })
  }
  const overview = useQuery<Overview>({
    queryKey: ['finance-workspace', 'overview', scope, month],
    queryFn: async () => (await api.get('/finance/overview', { params: { scope, month: selectedMonth } })).data,
  })
  const accounts = useQuery<Account[]>({
    queryKey: ['finance-workspace', 'accounts'],
    queryFn: async () => (await api.get('/finance/accounts')).data,
  })
  const plans = useQuery<Plan[]>({
    queryKey: ['finance-workspace', 'plans', scope],
    queryFn: async () => (await api.get('/finance/plans', { params: { scope } })).data,
  })
  const projection = useQuery<Projection[]>({
    queryKey: ['finance-workspace', 'projection', scope, month],
    queryFn: async () => (await api.get('/finance/projection', { params: { scope, start_month: selectedMonth, months: 6 } })).data,
  })
  const action = useMutation({
    mutationFn: async (task: () => Promise<unknown>) => task(),
    onSuccess: () => {
      setError('')
      setMessage('Registro salvo com sucesso.')
      refresh()
    },
    onError: (e: any) => {
      setMessage('')
      const detail = e?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Não foi possível salvar. Verifique os dados.')
    },
  })
  const run = (task: () => Promise<unknown>) => { setError(''); setMessage(''); action.mutate(task) }
  const scopedAccounts = (accounts.data || []).filter(a => a.scope === scope)
  const ownPlans = (plans.data || []).filter(p => p.planned_date.startsWith(month) && p.status === 'planned')
  const canRealize = movement.status === 'realized'
  const payer = scope === 'business' ? 'business' : movement.paid_by
  const selectedAccount = scopedAccounts.find(a => a.id === movement.account_id)

  const submitMovement = (e: React.FormEvent) => {
    e.preventDefault()
    const amount = Number(movement.amount)
    if (!Number.isFinite(amount) || amount <= 0) return setError('Informe um valor positivo.')
    if (movement.status === 'planned' && (!Number.isInteger(Number(movement.months)) || Number(movement.months) < 1 || Number(movement.months) > 24)) return setError('A recorrência deve ter de 1 a 24 meses.')
    if (!movement.title.trim()) return setError('Informe a descrição.')
    if (movement.status === 'planned') {
      run(async () => {
        await api.post('/finance/plans/recurring', {
          title: movement.title, amount, type: movement.type, scope,
          category: movement.category, first_due: movement.date,
          paid_by: payer, months: Number(movement.months),
        })
        setMovement({ ...movement, title: '', amount: '' })
      })
    } else {
      if (movement.account_id && payer !== 'self' && payer !== 'business') return setError('Gastos pagos por terceiros não podem movimentar sua conta.')
      if (movement.account_id && !selectedAccount) return setError('Selecione uma conta do contexto atual.')
      run(async () => {
        await api.post('/bills/create', {
          issuer: movement.title, amount, type: movement.type, scope,
          paid_by: payer, account_id: movement.account_id || null,
          due_date: movement.date, category: movement.category,
          status: 'paid', is_bill: false,
        })
        setMovement({ ...movement, title: '', amount: '' })
      })
    }
  }

  return <div className="mx-auto max-w-7xl space-y-5 p-3 sm:p-6">
    <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div>
        <p className="text-sm font-semibold text-blue-700">EconomizeIA</p>
        <h1 className="text-2xl font-bold text-gray-900">Gestão pessoal e PJ</h1>
        <p className="mt-1 text-sm text-gray-600">Planejamentos e metas não alteram o saldo até serem realizados.</p>
      </div>
      <div className="flex flex-wrap items-end gap-3">
        <div><Label>Contexto financeiro</Label>
          <select className={inputClass} value={scope} onChange={e => { setScope(e.target.value as Scope); setMovement(m => ({ ...m, account_id: '' })) }}>
            <option value="personal">Pessoal</option><option value="business">Empresa (PJ)</option>
          </select>
        </div>
        <div><Label>Mês de referência</Label>
          <input aria-label="Mês" type="month" className={inputClass} value={month} onChange={e => setMonth(e.target.value)} />
        </div>
      </div>
    </header>
    {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
    {message && <div role="status" className="rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-800">{message}</div>}
    {overview.isLoading ? <LoadingSpinner message="Carregando resumo..." /> : overview.isError ? <div className="text-sm text-red-700">Não foi possível carregar o resumo.</div> :
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat title="Receitas realizadas" amount={overview.data?.income || 0} />
        <Stat title="Despesas realizadas (seu dinheiro)" amount={overview.data?.expenses || 0} />
        <Stat title="Saldo do período" amount={overview.data?.balance || 0} />
        <Stat title="Custeado por terceiros" amount={overview.data?.third_party_expenses || 0} foot="Não reduz seu saldo." />
      </div>}
    <div className="grid gap-4 lg:grid-cols-2">
      <section className={section}>
        <div className="mb-3 flex items-center gap-2"><Plus size={19}/><h2 className="font-bold">Novo lançamento</h2></div>
        <form onSubmit={submitMovement} className="grid grid-cols-2 gap-3">
          <div className="col-span-2"><Label>Descrição</Label><input required maxLength={255} className={inputClass} placeholder="Ex.: Visão Promotora, aluguel, DAS" value={movement.title} onChange={e => setMovement({ ...movement, title: e.target.value })} /></div>
          <div><Label>Tipo</Label><select className={inputClass} value={movement.type} onChange={e => setMovement({ ...movement, type: e.target.value as MoneyType })}><option value="expense">Despesa</option><option value="income">Receita</option></select></div>
          <div><Label>Valor (R$)</Label><input required type="number" step="0.01" min="0.01" className={inputClass} value={movement.amount} onChange={e => setMovement({ ...movement, amount: e.target.value })}/></div>
          <div><Label>Data</Label><input required type="date" className={inputClass} value={movement.date} onChange={e => setMovement({ ...movement, date: e.target.value })}/></div>
          <div><Label>Categoria</Label><select className={inputClass} value={movement.category} onChange={e => setMovement({ ...movement, category: e.target.value })}>{categories.map(([key,label]) => <option key={key} value={key}>{label}</option>)}</select></div>
          <div><Label>Registro</Label><select className={inputClass} value={movement.status} onChange={e => setMovement({ ...movement, status: e.target.value })}><option value="planned">Planejamento (não movimenta saldo)</option><option value="realized">Realizado (movimenta saldo)</option></select></div>
          <div><Label>Quem paga</Label><select className={inputClass} disabled={scope === 'business'} value={payer} onChange={e => setMovement({ ...movement, paid_by: e.target.value as Payer, account_id: '' })}>{scope === 'business' ? <option value="business">Empresa</option> : <><option value="self">Eu</option><option value="family">Família</option><option value="other">Terceiros</option></>}</select></div>
          {canRealize ? <div className="col-span-2"><Label>Conta (opcional)</Label><select className={inputClass} value={movement.account_id} onChange={e => setMovement({ ...movement, account_id: e.target.value })}><option value="">Sem conta vinculada</option>{scopedAccounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}</select></div> :
            <div className="col-span-2"><Label>Repetir por quantos meses?</Label><input className={inputClass} type="number" min="1" max="24" value={movement.months} onChange={e => setMovement({ ...movement, months: e.target.value })}/><p className="mt-1 text-xs text-gray-500">Ex.: 6 meses para o contrato; 2 meses para a dívida.</p></div>}
          <div className="col-span-2"><button disabled={action.isPending} className={btn} type="submit">Salvar {canRealize ? 'movimentação' : 'planejamento'}</button></div>
        </form>
      </section>
      <section className={section}>
        <div className="mb-3 flex items-center gap-2"><Wallet size={19}/><h2 className="font-bold">Contas {scope === 'business' ? 'da empresa' : 'pessoais'}</h2></div>
        <div className="space-y-2">
          {scopedAccounts.map(a => <div className="flex justify-between rounded-lg bg-gray-50 p-3 text-sm" key={a.id}><span>{a.name}</span><strong>{money(a.calculated_balance)}</strong></div>)}
          {!scopedAccounts.length && <p className="text-sm text-gray-500">Nenhuma conta cadastrada ainda. Cadastre sua conta real para acompanhar saldos.</p>}
        </div>
        <form className="mt-4 grid gap-2 sm:grid-cols-3" onSubmit={e => {
          e.preventDefault()
          run(async () => { await api.post('/finance/accounts', { name: accountName, scope, type: scope === 'business' ? 'business' : 'checking', opening_balance: Number(openingBalance) }); setAccountName(''); setOpeningBalance('0') })
        }}>
          <div><Label>Nome da conta</Label><input required className={inputClass} value={accountName} placeholder={scope === 'business' ? 'Cora PJ' : 'Conta pessoal'} onChange={e => setAccountName(e.target.value)}/></div>
          <div><Label>Saldo inicial</Label><input required type="number" step="0.01" className={inputClass} value={openingBalance} onChange={e => setOpeningBalance(e.target.value)}/></div>
          <div className="self-end"><button type="submit" disabled={action.isPending} className={btn}>Adicionar conta</button></div>
        </form>
        <p className="mt-2 text-xs text-gray-500">Saldo calculado = saldo inicial + movimentações realizadas vinculadas + transferências. Não é sincronização bancária.</p>
      </section>
      <section className={section}>
        <div className="mb-3 flex items-center gap-2"><PiggyBank size={19}/><h2 className="font-bold">Limites do mês</h2></div>
        <div className="space-y-3">
          {(overview.data?.budgets || []).map(b => <div key={b.category}><div className="flex justify-between text-sm"><span>{b.category}</span><span>{money(b.spent)} / {money(b.limit)}</span></div><div className="mt-1 h-2 overflow-hidden rounded-full bg-gray-100"><div className={'h-full rounded-full ' + (b.remaining < 0 ? 'bg-red-500' : 'bg-blue-500')} style={{ width: Math.min(100, b.limit ? b.spent / b.limit * 100 : 0) + '%' }} /></div></div>)}
          {!overview.data?.budgets?.length && <p className="text-sm text-gray-500">Configure um limite para acompanhar seus gastos.</p>}
        </div>
        <form className="mt-4 grid gap-2 sm:grid-cols-3" onSubmit={e => {
          e.preventDefault()
          run(() => api.put('/finance/budgets', { scope, month: selectedMonth, category: budgetCategory, amount: Number(budgetAmount) }))
        }}>
          <div><Label>Categoria</Label><select className={inputClass} value={budgetCategory} onChange={e => setBudgetCategory(e.target.value)}>{categories.map(([key,label]) => <option key={key} value={key}>{label}</option>)}</select></div>
          <div><Label>Limite mensal</Label><input required type="number" min="0" step="0.01" className={inputClass} value={budgetAmount} onChange={e => setBudgetAmount(e.target.value)}/></div>
          <div className="self-end"><button className={btn} disabled={action.isPending}>Salvar limite</button></div>
        </form>
        <Link className="mt-3 inline-block text-sm font-semibold text-blue-700 underline" to="/app/savings-goals">Ver metas de reserva</Link>
      </section>
      <section className={section}>
        <div className="mb-3 flex items-center gap-2"><CalendarDays size={19}/><h2 className="font-bold">Previsões de {month}</h2></div>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="rounded-lg bg-green-50 p-3"><p className="text-green-700">A receber</p><strong>{money(overview.data?.planned_income || 0)}</strong></div>
          <div className="rounded-lg bg-amber-50 p-3"><p className="text-amber-700">A pagar</p><strong>{money(overview.data?.planned_expenses || 0)}</strong></div>
        </div>
        <div className="mt-3 max-h-72 space-y-2 overflow-auto">
          {ownPlans.map(plan => <div key={plan.id} className="flex items-center justify-between gap-2 rounded-lg border border-gray-100 p-2 text-sm">
            <div className="min-w-0"><p className="truncate font-medium">{plan.title}</p><p className="text-xs text-gray-500">{plan.planned_date} · {plan.paid_by === 'family' ? 'Paga pela família' : plan.type === 'income' ? 'Receita prevista' : 'Despesa prevista'}</p></div>
            <div className="flex shrink-0 items-center gap-2"><span>{money(plan.amount)}</span><button disabled={action.isPending} className={smallBtn} onClick={() => run(() => api.post('/finance/plans/' + plan.id + '/realize', {}))}>Realizar</button><button aria-label={'Cancelar ' + plan.title} disabled={action.isPending} className={smallBtn} onClick={() => run(() => api.delete('/finance/plans/' + plan.id))}>×</button></div>
          </div>)}
          {!ownPlans.length && <p className="text-sm text-gray-500">Nenhuma previsão pendente nesse mês.</p>}
        </div>
        <p className="mt-2 text-xs text-gray-500">Marcar como realizado cria um lançamento sem conta vinculada. Caso queira contabilizar na Cora ou em outra conta, registre um lançamento realizado diretamente no formulário, sem marcar a previsão como realizada.</p>
      </section>
    </div>
    <div className="grid gap-4 lg:grid-cols-2">
      <section className={section}>
        <div className="mb-3 flex items-center gap-2"><ArrowLeftRight size={19}/><h2 className="font-bold">Transferir entre suas contas</h2></div>
        <form className="grid gap-3 sm:grid-cols-2" onSubmit={e => {
          e.preventDefault()
          if (transfer.from_account_id === transfer.to_account_id) return setError('Escolha contas diferentes.')
          run(() => api.post('/finance/transfers', { ...transfer, amount: Number(transfer.amount) }))
        }}>
          <div><Label>Origem</Label><select required className={inputClass} value={transfer.from_account_id} onChange={e => setTransfer({ ...transfer, from_account_id: e.target.value })}><option value="">Selecione</option>{(accounts.data || []).map(a => <option key={a.id} value={a.id}>{a.name} ({a.scope === 'business' ? 'PJ' : 'Pessoal'})</option>)}</select></div>
          <div><Label>Destino</Label><select required className={inputClass} value={transfer.to_account_id} onChange={e => setTransfer({ ...transfer, to_account_id: e.target.value })}><option value="">Selecione</option>{(accounts.data || []).map(a => <option key={a.id} value={a.id}>{a.name} ({a.scope === 'business' ? 'PJ' : 'Pessoal'})</option>)}</select></div>
          <div><Label>Valor</Label><input type="number" min="0.01" step="0.01" required className={inputClass} value={transfer.amount} onChange={e => setTransfer({ ...transfer, amount: e.target.value })}/></div>
          <div><Label>Data</Label><input type="date" required className={inputClass} value={transfer.transferred_on} onChange={e => setTransfer({ ...transfer, transferred_on: e.target.value })}/></div>
          <div className="sm:col-span-2"><button className={btn} disabled={action.isPending}>Registrar transferência</button></div>
        </form>
        <p className="mt-2 text-xs text-gray-500">Transferências alteram os saldos das contas, mas nunca contam como receita nova ou despesa operacional. Retiradas PJ devem ser tratadas conforme orientação contábil.</p>
      </section>
      <section className={section}>
        <div className="mb-3 flex items-center gap-2"><Briefcase size={19}/><h2 className="font-bold">Projeção de seis meses — {scope === 'business' ? 'PJ' : 'Pessoal'}</h2></div>
        {projection.isLoading ? <LoadingSpinner message="Carregando projeção..." /> : projection.isError ? <p className="text-red-700">Falha ao carregar projeção.</p> :
        <div className="overflow-x-auto"><table className="w-full text-sm">
          <thead><tr className="border-b text-left text-gray-500"><th className="py-2">Mês</th><th>Entradas previstas</th><th>Saídas previstas</th><th>Resultado estimado*</th></tr></thead>
          <tbody>{(projection.data || []).map(row => <tr className="border-b" key={row.month}><td className="py-2">{row.month.slice(0,7)}</td><td>{money(row.future_income)}</td><td>{money(row.future_expenses)}</td><td className={row.projected_net < 0 ? 'text-red-700' : 'text-green-700'}>{money(row.projected_net)}</td></tr>)}</tbody>
        </table></div>}
        <p className="mt-3 text-xs text-gray-500">*Resultado do período = movimentações realizadas + previsões pendentes. Não inclui custos ainda não cadastrados nem é saldo bancário.</p>
      </section>
    </div>
  </div>
}
