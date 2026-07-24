import { addMonths, format, isSameMonth, startOfMonth, subMonths } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { CalendarDays, ChevronLeft, ChevronRight, RotateCcw } from 'lucide-react'

interface MonthSelectorProps {
  value: Date
  onChange: (date: Date) => void
  className?: string
  compact?: boolean
}

export default function MonthSelector({ value, onChange, className = '', compact = false }: MonthSelectorProps) {
  const currentMonth = startOfMonth(new Date())
  const selectedMonth = startOfMonth(value)
  const canReset = !isSameMonth(selectedMonth, currentMonth)
  const label = format(selectedMonth, 'MMMM yyyy', { locale: ptBR })

  return (
    <div className={`flex flex-wrap items-center gap-2 ${className}`}>
      <div className="inline-flex min-h-[40px] items-center overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <button
          type="button"
          onClick={() => onChange(subMonths(selectedMonth, 1))}
          className="flex h-10 w-10 items-center justify-center text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-950"
          aria-label="Mês anterior"
          title="Mês anterior"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <div className="flex h-10 min-w-[160px] items-center justify-center gap-2 border-x border-slate-200 px-3 text-sm font-semibold capitalize text-slate-950">
          {!compact && <CalendarDays className="h-4 w-4 text-slate-500" />}
          {label}
        </div>
        <button
          type="button"
          onClick={() => onChange(addMonths(selectedMonth, 1))}
          className="flex h-10 w-10 items-center justify-center text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-950"
          aria-label="Próximo mês"
          title="Próximo mês"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
      {canReset && (
        <button
          type="button"
          onClick={() => onChange(currentMonth)}
          className="inline-flex h-10 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 shadow-sm transition-colors hover:bg-slate-50 hover:text-slate-950"
        >
          <RotateCcw className="h-4 w-4" />
          Hoje
        </button>
      )}
    </div>
  )
}
