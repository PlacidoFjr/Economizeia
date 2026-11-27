import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Trash2 } from 'lucide-react'
import api from '../services/api'
import ConfirmDialog from './ConfirmDialog'
import { translateCategory } from '../utils/translations'

type Kind = 'income' | 'expense' | 'budget' | 'reserve'
type Payer = 'self' | 'third' | 'shared'
type Frequency = 'once' | 'weekly' | 'monthly' | 'yearly' | 'actual'
type Plan = {
  id: string
  version: string
  name: string
  amount_cents: number
  kind: Kind
  payer: Payer
  frequency: Frequency
  month: string
  day?: string | null
  until?: string | null
  months?: number | null
  category?: string
  account?: string | null
  payer_name?: string | null
  personal_cents?: number | null
}
type Edit = Omit<Plan, 'id'>

const kinds: Record<Kind, string> = { income: 'Receita prevista', expense: 'Despesa', budget: 'Limite de orçamento', reserve: 'Meta de reserva' }
const frequencies: Record<Frequency, string> = { once: 'Pontual', weekly: 'Semanal', monthly: 'Mensal', yearly: 'Anual', actual: 'Realizado / guardado' }
const categories = ['alimentacao', 'moradia', 'servicos', 'transporte', 'saude', 'lazer', 'educacao', 'impostos', 'dividas', 'investimentos', 'outras']
const extraCategories: Record<string, string> = { lazer: 'Lazer', educacao: 'Educação', impostos: 'Impostos', dividas: 'Dívidas' }
const inputClass = 'mt-1 block min-h-10 w-full min-w-0 rounded-md border border-slate-300 bg-white px-2.5 py-2 text-sm dark:border-slate-600 dark:bg-slate-950'
const secondary = 'inline-flex min-h-10 items-center justify-center gap-1.5 rounded-md border border-slate-300 px-3 text-sm font-semibold hover:bg-slate-100 disabled:opacity-50 dark:border-slate-600 dark:hover:bg-slate-800'
const currency = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const monthLabel = new Intl.DateTimeFormat('pt-BR', { month: 'long', year: 'numeric', timeZone: 'UTC' })
const centsInput = (cents?: number | null) => cents == null ? '' : (cents / 100).toFixed(2).replace('.', ',')
const displayDate = (iso: string) => iso.split('-').reverse().join('/')

function parseCents(text: string) {
  const value = text.trim()
  const groups = value.match(/^(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{1,2}))?$/)
  const normalized = groups ? groups[1].replace(/\./g, '') + '.' + (groups[2] || '00') : value
  if (!/^\d+(?:\.\d{1,2})?$/.test(normalized)) return 0
  const [units, fraction = ''] = normalized.split('.')
  const cents = Number(units) * 100 + Number(fraction.padEnd(2, '0'))
  return Number.isSafeInteger(cents) && cents <= 10000000000 ? cents : 0
}

function errorMessage(error: unknown) {
  const detail = (error as { response?: { data?: { detail?: unknown } } } | undefined)?.response?.data?.detail
  return typeof detail === 'string' ? detail : 'Não foi possível salvar a alteração. Confira os campos e tente novamente.'
}

function PlanForm({ item, busy, error, onCancel, onSave }: {
  item: Plan
  busy: boolean
  error: string
  onCancel: () => void
  onSave: (edit: Edit) => void
}) {
  const [form, setForm] = useState(item)
  const [amount, setAmount] = useState(centsInput(item.amount_cents))
  const [personal, setPersonal] = useState(centsInput(item.personal_cents))
  const [validation, setValidation] = useState('')
  const nameRef = useRef<HTMLInputElement>(null)
  useEffect(() => { nameRef.current?.focus() }, [])

  const field = <K extends keyof Plan>(key: K, value: Plan[K]) => setForm(current => ({ ...current, [key]: value }))
  const recurring = ['weekly', 'monthly', 'yearly'].includes(form.frequency)
  const canMarkActual = (form.kind === 'expense' && form.payer === 'third') || form.kind === 'reserve'
  const categoryOptions = [...new Set([...categories, form.category || 'outras'])]

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const cents = parseCents(amount)
    const share = form.payer === 'shared' ? parseCents(personal) : null
    if (!cents || share === 0 || (share !== null && share >= cents)) {
      setValidation('Informe um valor válido. Sua parte deve ser menor que o total.')
      return
    }
    setValidation('')
    const { version, kind, name, payer, frequency, month, day, category, account, payer_name, until, months } = form
    onSave({
      version, kind, payer, frequency, name: name.trim(), amount_cents: cents, personal_cents: share,
      month: day?.slice(0, 7) || month, day: day || null, category: category || 'outras',
      account: kind === 'income' || (kind === 'expense' && payer !== 'self') ? account || null : null,
      payer_name: payer !== 'self' ? payer_name || null : null,
      until: recurring ? until || null : null,
      months: frequency === 'monthly' ? months || null : null,
    })
  }

  return (
    <form onSubmit={submit} className="mb-4 rounded-lg border border-teal-200 bg-teal-50/60 p-3 dark:border-teal-900 dark:bg-slate-950 sm:p-4">
      <h3 className="text-base font-semibold">Editar item</h3>
      <fieldset disabled={busy} className="mt-3 grid min-w-0 gap-3 text-sm sm:grid-cols-2">
        <label className="sm:col-span-2">Descrição
          <input ref={nameRef} required maxLength={180} className={inputClass} value={form.name} onChange={e => field('name', e.target.value)} />
        </label>
        <label>Valor por ocorrência (R$)
          <input inputMode="decimal" required className={inputClass} value={amount} onChange={e => setAmount(e.target.value)} />
        </label>
        <label>Tipo
          <select className={inputClass} value={form.kind} onChange={e => {
            const kind = e.target.value as Kind
            setForm(current => ({ ...current, kind, payer: kind === 'expense' ? current.payer : 'self',
              frequency: !['expense', 'reserve'].includes(kind) && current.frequency === 'actual' ? 'once' : current.frequency }))
          }}>
            {Object.entries(kinds).map(([value, title]) => <option key={value} value={value}>{title}</option>)}
          </select>
        </label>
        <label>Frequência
          <select className={inputClass} value={form.frequency} onChange={e => field('frequency', e.target.value as Frequency)}>
            {Object.entries(frequencies).filter(([value]) => value !== 'actual' || canMarkActual).map(([value, title]) => (
              <option key={value} value={value}>{title}</option>
            ))}
          </select>
        </label>
        <label>Mês inicial
          <input type="month" required min="2000-01" max="2099-12" className={inputClass} value={form.month} onChange={e => {
            const month = e.target.value
            setForm(current => ({ ...current, month, day: current.day?.startsWith(month + '-') ? current.day : null }))
          }} />
        </label>
        <label>{form.frequency === 'actual' ? 'Data do pagamento ou reserva' : 'Primeira data ou vencimento'}
          <input type="date" required={form.frequency === 'weekly' || form.frequency === 'actual'} className={inputClass} value={form.day || ''} onChange={e => {
            const day = e.target.value
            setForm(current => ({ ...current, day, month: day ? day.slice(0, 7) : current.month }))
          }} />
        </label>
        <label>Categoria
          <select className={inputClass} value={form.category || 'outras'} onChange={e => field('category', e.target.value)}>
            {categoryOptions.map(value => <option key={value} value={value}>{extraCategories[value] || translateCategory(value)}</option>)}
          </select>
        </label>
        {recurring && <label>Data final (opcional)
          <input type="date" className={inputClass} value={form.until || ''} onChange={e => setForm(current => ({ ...current, until: e.target.value, months: e.target.value ? null : current.months }))} />
        </label>}
        {form.frequency === 'monthly' && <label>Quantidade de meses (opcional)
          <input type="number" min={1} max={120} step={1} className={inputClass} value={form.months ?? ''} onChange={e => {
            const months = e.target.value ? Number(e.target.value) : null
            setForm(current => ({ ...current, months, until: months ? null : current.until }))
          }} />
        </label>}
        {form.kind === 'income' && <label>Conta de recebimento (opcional)
          <input maxLength={100} className={inputClass} value={form.account || ''} onChange={e => field('account', e.target.value)} />
        </label>}
        {form.kind === 'expense' && <label>Responsável
          <select className={inputClass} value={form.payer} onChange={e => {
            const payer = e.target.value as Payer
            setForm(current => ({ ...current, payer, frequency: payer !== 'third' && current.frequency === 'actual' ? 'once' : current.frequency }))
          }}>
            <option value="self">Despesas próprias</option><option value="third">Terceiros</option><option value="shared">Compartilhado</option>
          </select>
        </label>}
        {form.payer !== 'self' && <label>Nome do responsável (opcional)
          <input maxLength={100} className={inputClass} value={form.payer_name || ''} onChange={e => field('payer_name', e.target.value)} />
        </label>}
        {form.payer === 'shared' && <label>Sua parte (R$)
          <input required inputMode="decimal" className={inputClass} value={personal} onChange={e => setPersonal(e.target.value)} />
        </label>}
      </fieldset>
      {form.frequency !== 'once' && form.frequency !== 'actual' && (
        <p className="mt-3 text-xs text-slate-600">As alterações se aplicam à série. Pagamentos já registrados continuam no histórico.</p>
      )}
      {(validation || error) && <p className="mt-3 text-sm text-red-700 dark:text-red-300" role="alert">{validation || error}</p>}
      <div className="mt-4 flex flex-wrap gap-2">
        <button disabled={busy} className="min-h-10 rounded-md bg-teal-800 px-4 text-sm font-semibold text-white hover:bg-teal-900 disabled:opacity-50">Salvar alterações</button>
        <button type="button" disabled={busy} className={secondary} onClick={onCancel}>Cancelar</button>
      </div>
    </form>
  )
}

export default function FinancialPlanManager() {
  const client = useQueryClient()
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Plan | null>(null)
  const [deleting, setDeleting] = useState<Plan | null>(null)
  const [status, setStatus] = useState('')
  const plans = useQuery({
    queryKey: ['financial-plan-items'], enabled: open,
    queryFn: async () => (await api.get<Plan[]>('/chatbot/plan-items')).data,
  })
  const refresh = () => Promise.all(['financial-plan-items', 'financial-overview', 'bills', 'finances', 'payments', 'installment-bills']
    .map(key => client.invalidateQueries({ queryKey: [key] })))
  const save = useMutation({
    mutationFn: ({ id, ...edit }: Edit & { id: string }) => api.put('/chatbot/plan-items/' + id, edit),
    onSuccess: async () => {
      await refresh()
      setEditing(null)
      setStatus('Item atualizado.')
    },
  })
  const remove = useMutation({
    mutationFn: (item: Plan) => api.delete('/chatbot/plan-items/' + item.id, { params: { version: item.version } }),
    onSuccess: async () => {
      await refresh()
      setDeleting(null)
      setStatus('Item excluído.')
    },
    onError: () => setDeleting(null),
  })
  const busy = save.isPending || remove.isPending
  const conflict = (error: unknown) => (error as { response?: { status?: number } } | undefined)?.response?.status === 409

  return (
    <div>
      <button type="button" className={secondary} aria-expanded={open} disabled={busy} onClick={() => {
        setOpen(value => !value)
        if (open) setEditing(null)
      }}><Pencil size={15} aria-hidden="true" /> Gerenciar planejamento</button>
      {open && <div className="mt-3 space-y-3">
        <p className="text-sm text-slate-600">Itens de todos os meses, incluindo os cadastrados pelo chat.</p>
        {status && <p role="status" className="text-sm font-semibold text-teal-800 dark:text-teal-200">{status}</p>}
        {plans.isPending && <p className="text-sm">Carregando itens...</p>}
        {plans.isError && <div role="alert" className="text-sm">
          Não foi possível carregar os itens. <button type="button" className="font-semibold underline" onClick={() => plans.refetch()}>Tentar novamente</button>
        </div>}
        {remove.isError && <p role="alert" className="text-sm text-red-700 dark:text-red-300">{errorMessage(remove.error)}</p>}
        {editing && <PlanForm key={editing.id} item={editing} busy={busy} error={save.isError ? errorMessage(save.error) : ''} onCancel={() => {
          setEditing(null)
          if (conflict(save.error)) void plans.refetch()
        }} onSave={values => save.mutate({ id: editing.id, ...values })} />}
        {plans.data?.length === 0 && <p className="text-sm text-slate-600">Nenhum item cadastrado.</p>}
        {!!plans.data?.length && <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 dark:divide-slate-700 dark:border-slate-700">
          {plans.data.map(item => (
            <li key={item.id} className="flex flex-wrap items-center justify-between gap-2 px-3 py-2">
              <div className="min-w-0 flex-1">
                <p className="break-words text-sm font-semibold">{item.name}</p>
                <p className="text-sm text-slate-600">
                  {currency.format(item.amount_cents / 100)} · {kinds[item.kind]} · {frequencies[item.frequency]} · {item.day ? displayDate(item.day) : monthLabel.format(new Date(item.month + '-01T12:00:00Z'))}
                </p>
              </div>
              <div className="flex flex-wrap gap-1.5">
                <button type="button" className={secondary} disabled={busy || editing?.id === item.id} aria-label={'Editar ' + item.name} onClick={() => {
                  setStatus('')
                  save.reset()
                  setEditing(item)
                }}>Editar</button>
                <button type="button" className={secondary} disabled={busy} aria-label={'Excluir ' + item.name} onClick={() => {
                  setStatus('')
                  remove.reset()
                  setDeleting(item)
                }}><Trash2 size={15} aria-hidden="true" /></button>
              </div>
            </li>
          ))}
        </ul>}
      </div>}
      <ConfirmDialog open={!!deleting} title="Excluir item do planejamento?" tone="danger" confirmLabel="Excluir"
        description={'O item “' + (deleting?.name || '') + '” será removido de todo o planejamento, junto com os compromissos em aberto gerados por ele. Pagamentos já registrados continuam no histórico.'}
        isLoading={remove.isPending} onCancel={() => { if (!remove.isPending) setDeleting(null) }}
        onConfirm={() => {
          if (deleting) {
            if (editing?.id === deleting.id) setEditing(null)
            remove.mutate(deleting)
          }
        }} />
    </div>
  )
}

