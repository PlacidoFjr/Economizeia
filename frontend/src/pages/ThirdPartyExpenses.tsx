import { useState, useRef, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { format, startOfMonth } from 'date-fns'
import { CreditCard, Plus, Wallet, TrendingUp, Pencil, Trash2 } from 'lucide-react'
import api from '../services/api'
import MonthSelector from '../components/MonthSelector'
import ConfirmDialog from '../components/ConfirmDialog'
import { translateCategory } from '../utils/translations'

type Entry = { id: string; version: string; name: string; amount_cents: number; total_cents: number; category: string; frequency: string; month: string; day?: string | null; payer_name?: string | null; account?: string | null; father_card: boolean; editable: boolean }
type Overview = { month: string; limit_cents: number | null; card_spent_cents: number; card_remaining_cents: number | null; card_planned_cents: number; actual_cents: number; planned_cents: number; card_categories: Record<string, number>; actual: Entry[]; planned: Entry[] }
const money = (cents: number) => (cents / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const moneyInput = (cents: number) => (cents / 100).toFixed(2).replace('.', ',')
function parseCents(value: string): number | null {
  const trimmed = value.trim()
  const match = trimmed.match(/^(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{1,2}))?$/)
  const normalized = match ? match[1].replace(/\./g, '') + '.' + (match[2] || '00') : trimmed
  if (!/^\d+(?:\.\d{1,2})?$/.test(normalized)) return null
  const [units, fraction = ''] = normalized.split('.')
  const cents = Number(units) * 100 + Number(fraction.padEnd(2, '0'))
  return Number.isSafeInteger(cents) && cents <= 10000000000 ? cents : null
}
const card = 'rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5 dark:border-slate-800 dark:bg-slate-900'
const input = 'mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm dark:border-slate-700 dark:bg-slate-950'
const primary = 'inline-flex min-h-10 items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50 dark:bg-white dark:text-slate-950'
const secondary = 'inline-flex min-h-10 items-center justify-center gap-2 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium disabled:opacity-50 dark:border-slate-700'
const categories = ['alimentacao', 'moradia', 'servicos', 'transporte', 'saude', 'lazer', 'educacao', 'impostos', 'dividas', 'outras']
const frequency: Record<string, string> = { monthly: 'Mensal', weekly: 'Semanal', yearly: 'Anual', once: 'Pontual', actual: 'Realizada' }
function errorText(error: unknown) {
  const detail = (error as { response?: { data?: { detail?: unknown } } } | undefined)?.response?.data?.detail
  return typeof detail === 'string' ? detail : 'Não foi possível concluir. Tente novamente.'
}

export default function ThirdPartyExpenses() {
  const client = useQueryClient()
  const [month, setMonth] = useState(startOfMonth(new Date()))
  const key = format(month, 'yyyy-MM')
  const query = useQuery<Overview>({
    queryKey: ['third-party-expenses', key],
    queryFn: async () => (await api.get('/chatbot/third-party', { params: { month: key } })).data,
    staleTime: 0,
  })
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Entry | null>(null)
  const [deleting, setDeleting] = useState<Entry | null>(null)
  const [limitInput, setLimitInput] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [amount, setAmount] = useState('')
  const [day, setDay] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [category, setCategory] = useState('outras')
  const [fatherCard, setFatherCard] = useState(true)
  const [payer, setPayer] = useState('')
  const [error, setError] = useState('')
  const requestId = useRef('')
  const refresh = async () => {
    await Promise.all(['third-party-expenses', 'financial-overview', 'financial-plan-items', 'dashboard', 'finances'].map(k => client.invalidateQueries({ queryKey: [k] })))
  }
  const saveLimit = useMutation({
    mutationFn: async (value: number | null) => api.put('/chatbot/third-party/limit', { amount_cents: value }, { params: { month: key } }),
    onSuccess: async () => { setLimitInput(null); setError(''); await refresh() },
    onError: err => setError(errorText(err)),
  })
  const saveEntry = useMutation({
    mutationFn: async (cents: number) => {
      if (editing) {
        await api.put('/chatbot/plan-items/' + editing.id, {
          version: editing.version, name: name.trim(), amount_cents: cents, kind: 'expense', payer: 'third',
          frequency: 'actual', month: day.slice(0, 7), day, category,
          account: fatherCard ? 'Cartão do pai' : null, payer_name: fatherCard ? 'Pai' : payer.trim(),
          personal_cents: null, months: null, until: null,
        })
      } else {
        await api.post('/chatbot/third-party/entries', { request_id: requestId.current, name: name.trim(), amount_cents: cents, day, category, father_card: fatherCard, payer_name: fatherCard ? null : payer.trim() })
      }
    },
    onSuccess: async () => {
      setMonth(startOfMonth(new Date(day + 'T12:00:00')))
      setShowForm(false); setEditing(null); setError(''); await refresh()
    },
    onError: err => setError(errorText(err)),
  })
  const funding = useMutation({
    mutationFn: async (entry: Entry) => api.patch('/chatbot/third-party/entries/' + entry.id + '/funding', { version: entry.version, father_card: !entry.father_card }),
    onSuccess: refresh, onError: err => setError(errorText(err)),
  })
  const remove = useMutation({
    mutationFn: async (entry: Entry) => api.delete('/chatbot/plan-items/' + entry.id, { params: { version: entry.version } }),
    onSuccess: async () => { setDeleting(null); await refresh() },
    onError: err => { setDeleting(null); setError(errorText(err)) },
  })
  const busy = saveEntry.isPending || saveLimit.isPending || funding.isPending || remove.isPending
  function openForm(entry?: Entry) {
    setError(''); setEditing(entry || null); setName(entry?.name || ''); setAmount(entry ? moneyInput(entry.amount_cents) : '')
    const today = format(new Date(), 'yyyy-MM-dd')
    setDay(entry?.day || (key === today.slice(0, 7) ? today : key < today.slice(0, 7) ? key + '-01' : today))
    setCategory(entry?.category || 'outras'); setFatherCard(entry?.father_card ?? true); setPayer(entry?.payer_name || '')
    requestId.current = crypto.randomUUID()
    setShowForm(true)
  }
  function submit(event: FormEvent) {
    event.preventDefault()
    const cents = parseCents(amount)
    if (!cents || !name.trim() || (!fatherCard && !payer.trim())) { setError('Confira a descrição, o valor e o responsável.'); return }
    setError(''); saveEntry.mutate(cents)
  }
  const data = query.data
  // A forecast reserves part of the user's spending cap, but is not a realized purchase.
  const committed = data ? data.card_spent_cents + data.card_planned_cents : 0
  const limit = data?.limit_cents ?? null
  const remaining = limit === null ? null : limit - committed
  const percent = limit !== null && limit > 0 ? committed / limit * 100 : null
  const actualWidth = limit !== null && limit > 0 && data ? Math.min(100, data.card_spent_cents / limit * 100) : 0
  const plannedWidth = limit !== null && limit > 0 && data ? Math.min(100 - actualWidth, data.card_planned_cents / limit * 100) : 0
  function renderRows(entries: Entry[], planned: boolean) {
    if (!entries.length) return <p className="py-5 text-center text-sm text-slate-500">Nenhuma despesa {planned ? 'prevista' : 'realizada'} neste mês.</p>
    return <div className="divide-y divide-slate-200 dark:divide-slate-800">{entries.map(entry => <div key={entry.id} className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0"><p className="font-semibold break-words">{entry.name}</p><p className="text-xs text-slate-500">{translateCategory(entry.category)} · {planned ? frequency[entry.frequency] || entry.frequency : entry.day?.split('-').reverse().join('/') || 'Realizada'} · {entry.payer_name || 'Responsável não informado'}</p><p className="mt-1 text-xs font-medium text-slate-600 dark:text-slate-400">{entry.father_card ? 'Cartão do pai' : 'Cartão não identificado'}</p></div>
      <div className="flex flex-wrap items-center gap-2 sm:justify-end"><span className="font-semibold tabular-nums">{money(entry.total_cents)}</span>
        {entry.editable && <button type="button" disabled={busy} className={secondary + ' text-xs'} onClick={() => { setError(''); funding.mutate(entry) }}>{entry.father_card ? 'Retirar do cartão' : 'Vincular ao cartão'}</button>}
        {!planned && entry.editable && <><button type="button" disabled={busy} aria-label={'Editar ' + entry.name} className={secondary} onClick={() => openForm(entry)}><Pencil className="h-4 w-4" /></button><button type="button" disabled={busy} aria-label={'Excluir ' + entry.name} className={secondary} onClick={() => setDeleting(entry)}><Trash2 className="h-4 w-4 text-red-600" /></button></>}
      </div>
    </div>)}</div>
  }
  return <div className="space-y-5 text-slate-900 dark:text-slate-100">
    <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Controle separado</p><h1 className="text-2xl font-bold sm:text-3xl">Despesas de terceiros</h1><p className="mt-1 text-sm text-slate-500">Acompanhe gastos pagos por outras pessoas sem reduzir seu saldo pessoal.</p></div><button className={primary} onClick={() => openForm()}><Plus className="h-4 w-4" /> Nova compra</button></header>
    <MonthSelector value={month} onChange={value => { setMonth(value); setLimitInput(null); setError('') }} />
    {error && <p role="alert" className="rounded-lg border border-red-200 p-3 text-sm text-red-700 dark:text-red-300">{error}</p>}
    {showForm && <form onSubmit={submit} className={card + ' space-y-4'}><h2 className="font-bold">{editing ? 'Editar compra' : 'Registrar compra realizada'}</h2>
      <fieldset disabled={busy} className="grid gap-3 sm:grid-cols-2 text-sm">
        <label>Descrição<input className={input} required maxLength={180} value={name} onChange={e => setName(e.target.value)} /></label>
        <label>Valor (R$)<input className={input} inputMode="decimal" required value={amount} onChange={e => setAmount(e.target.value)} placeholder="0,00" /></label>
        <label>Data da compra<input className={input} type="date" required max={format(new Date(), 'yyyy-MM-dd')} min="2000-01-01" value={day} onChange={e => setDay(e.target.value)} /></label>
        <label>Categoria<select className={input} value={category} onChange={e => setCategory(e.target.value)}>{[...new Set([...categories, category])].map(c => <option key={c} value={c}>{translateCategory(c)}</option>)}</select></label>
        <label>Quem pagou<select className={input} value={fatherCard ? 'card' : 'other'} onChange={e => setFatherCard(e.target.value === 'card')}><option value="card">Cartão do pai</option><option value="other">Outro pagamento de terceiros</option></select></label>
        {!fatherCard && <label>Responsável<input className={input} required maxLength={100} value={payer} onChange={e => setPayer(e.target.value)} placeholder="Ex.: Pai, mãe" /></label>}
      </fieldset><p className="text-xs text-slate-500">Este lançamento não entra como despesa própria. Não há integração automática com a fatura do banco.</p><div className="flex flex-wrap gap-2"><button className={primary} disabled={busy} type="submit">{saveEntry.isPending ? 'Salvando...' : 'Salvar compra'}</button><button className={secondary} disabled={busy} type="button" onClick={() => { setShowForm(false); setEditing(null); setError('') }}>Cancelar</button></div>
    </form>}
    {query.isLoading && <p className={card}>Carregando despesas...</p>}
    {query.isError && <div className={card}><p>Não foi possível carregar as despesas.</p><button className={secondary + ' mt-2'} onClick={() => query.refetch()}>Tentar novamente</button></div>}
    {data && <>
      <section className="grid gap-3 sm:grid-cols-3">
        <div className={card + ' sm:col-span-3'}><div className="flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-2"><CreditCard className="h-5 w-5" /><h2 className="font-bold">Cartão do pai</h2></div><button className={secondary} disabled={busy} onClick={() => setLimitInput(data.limit_cents == null ? '' : moneyInput(data.limit_cents))}>{data.limit_cents == null ? 'Definir limite' : 'Editar limite'}</button></div>
          {limitInput !== null && <form className="mt-3 flex flex-wrap items-end gap-2" onSubmit={e => { e.preventDefault(); const cents = parseCents(limitInput); if (cents === null) { setError('Informe um limite válido.'); return } saveLimit.mutate(cents) }}><label className="text-sm">Limite para este mês (R$)<input className={input} inputMode="decimal" required value={limitInput} onChange={e => setLimitInput(e.target.value)} /></label><button className={primary} disabled={busy}>Salvar limite</button><button className={secondary} type="button" disabled={busy} onClick={() => setLimitInput(null)}>Cancelar</button>{data.limit_cents !== null && <button className={secondary} type="button" disabled={busy} onClick={() => saveLimit.mutate(null)}>Remover limite</button>}</form>}
          <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">{[['Compras registradas', money(data.card_spent_cents)], ['Limite de controle', data.limit_cents == null ? 'Não definido' : money(data.limit_cents)], ['Disponível após previsões', remaining === null ? '—' : money(remaining)], ['Despesas previstas vinculadas', money(data.card_planned_cents)]].map(([label, value]) => <div key={label}><p className="text-xs text-slate-500">{label}</p><p className="mt-1 text-lg font-bold tabular-nums sm:text-xl">{value}</p></div>)}</div>
          {percent !== null && <div className="mt-4">
            <div className="flex h-2.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800" role="img" aria-label={percent.toFixed(2).replace('.', ',') + '% do limite comprometido'}>
              <div style={{ width: actualWidth + '%' }} className="h-full shrink-0 bg-teal-500" />
              <div style={{ width: plannedWidth + '%' }} className="h-full shrink-0 bg-amber-500" />
            </div>
            <p className="mt-2 text-xs text-slate-500">{percent.toFixed(2).replace('.', ',')}% do limite comprometido · {money(committed)}{percent >= 100 ? ' · Limite atingido ou ultrapassado' : percent >= 80 ? ' · Atenção ao limite' : ''}</p>
            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
              <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-teal-500" />Realizado</span>
              <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-amber-500" />Previsto</span>
              <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-slate-200 dark:bg-slate-800" />Disponível</span>
            </div>
          </div>}
          {limit === 0 && <p className="mt-2 text-xs text-slate-500">Limite de controle definido em zero.</p>}
          {remaining !== null && remaining < 0 && <p className="mt-2 text-sm font-semibold text-red-600">Comprometimento acima do limite em {money(-remaining)}.</p>}
          <p className="mt-3 text-xs text-slate-500">Limite manual por mês civil. Compras realizadas e previsões vinculadas comprometem o limite. Confira se uma previsão já foi registrada como compra para não contabilizar a mesma despesa duas vezes.</p>
        </div>
        <div className={card}><Wallet className="mb-2 h-5 w-5 text-slate-500" /><p className="text-xs text-slate-500">Terceiros · despesas realizadas</p><p className="text-xl font-bold">{money(data.actual_cents)}</p></div>
        <div className={card}><TrendingUp className="mb-2 h-5 w-5 text-slate-500" /><p className="text-xs text-slate-500">Terceiros · despesas previstas</p><p className="text-xl font-bold">{money(data.planned_cents)}</p></div>
        <div className={card}><p className="text-xs text-slate-500">Compras no cartão</p><p className="mt-2 text-xl font-bold">{data.actual.filter(i => i.father_card).length}</p></div>
      </section>
      {Object.keys(data.card_categories).length > 0 && <section className={card}><h2 className="font-bold">Cartão por categoria</h2><div className="mt-4 space-y-3">{Object.entries(data.card_categories).sort((a,b) => b[1]-a[1]).map(([cat, cents]) => <div key={cat}><div className="flex justify-between gap-2 text-sm"><span>{translateCategory(cat)}</span><span className="font-medium">{money(cents)}</span></div><div className="mt-1 h-2 rounded-full bg-slate-200 dark:bg-slate-800"><div className="h-2 rounded-full bg-teal-500" style={{ width: (cents / data.card_spent_cents * 100) + '%' }} /></div></div>)}</div></section>}
      <section className={card}><h2 className="font-bold">Compras e despesas realizadas</h2>{renderRows(data.actual, false)}</section>
      <section className={card}><h2 className="font-bold">Despesas previstas e recorrentes</h2><p className="mt-1 text-xs text-slate-500">Registros existentes no planejamento. Vincule apenas os que realmente utilizam o cartão.</p>{renderRows(data.planned, true)}</section>
    </>}
    <ConfirmDialog open={!!deleting} title="Excluir compra?" description={'Remover ' + (deleting?.name || '') + ' do histórico de terceiros?'} confirmLabel="Excluir" tone="danger" isLoading={remove.isPending} onCancel={() => setDeleting(null)} onConfirm={() => { if (deleting) remove.mutate(deleting) }} />
  </div>
}
