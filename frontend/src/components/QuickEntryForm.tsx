import { useState, type FormEvent } from 'react'
import { format } from 'date-fns'

export type QuickEntry = { kind: 'expense' | 'income'; name: string; amount_cents: number; day: string; notes?: string }
const input = 'mt-1 block min-h-10 w-full rounded-md border border-slate-300 bg-white px-2.5 py-2 text-sm dark:border-slate-600 dark:bg-slate-900'
export default function QuickEntryForm({ kind, onSubmit, onCancel }: {
  kind: QuickEntry['kind']; onSubmit: (entry: QuickEntry) => void; onCancel: () => void
}) {
  const [name, setName] = useState('')
  const [amount, setAmount] = useState('')
  const [day, setDay] = useState(() => format(new Date(), 'yyyy-MM-dd'))
  const [error, setError] = useState('')
  const [notes, setNotes] = useState('')
  const today = format(new Date(), 'yyyy-MM-dd')
  function submit(event: FormEvent) {
    event.preventDefault()
    const value = amount.trim().replace(/\.(?=\d{3}(?:[.,]|$))/g, '').replace(',', '.')
    if (!/^\d+(?:\.\d{1,2})?$/.test(value)) { setError('Informe o valor com até duas casas decimais.'); return }
    const [units, fraction = ''] = value.split('.')
    const cents = Number(units) * 100 + Number(fraction.padEnd(2, '0'))
    if (!name.trim() || cents <= 0 || cents > 10000000000 || day > today) {
      setError('Confira a descrição, o valor e a data.')
      return
    }
    onSubmit({ kind, name: name.trim(), amount_cents: cents, day, notes: notes.trim() || undefined })
  }
  return <form onSubmit={submit} className="space-y-2 text-sm">
    <p className="font-semibold">{kind === 'expense' ? 'Gasto extra do mês' : 'Receita do mês'}</p>
    <label className="block">Descrição
      <input autoFocus required maxLength={180} className={input} value={name} onChange={e => setName(e.target.value)} placeholder={kind === 'expense' ? 'Ex. conserto do celular' : 'Ex. venda ou pagamento recebido'} />
    </label>
    <div className="grid min-w-0 grid-cols-2 gap-2">
      <label>Valor (R$)<input required inputMode="decimal" className={input} placeholder="0,00" value={amount} onChange={e => setAmount(e.target.value)} /></label>
      <label>Data<input required type="date" max={today} className={input} value={day} onChange={e => setDay(e.target.value)} /></label>
    </div>
    <label className="block">Detalhes para lembrar (opcional)
      <textarea rows={2} maxLength={2000} className={input} value={notes} onChange={e => setNotes(e.target.value)} placeholder="Ex. café, pão e produtos de limpeza" />
    </label>
    {error && <p role="alert" className="text-red-700 dark:text-red-300">{error}</p>}
    <div className="flex gap-2 pt-1">
      <button className="min-h-10 rounded-md bg-teal-800 px-3 font-semibold text-white">Revisar lançamento</button>
      <button type="button" className="min-h-10 rounded-md border border-slate-300 px-3" onClick={onCancel}>Cancelar</button>
    </div>
  </form>
}

