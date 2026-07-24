import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { endOfMonth, format, startOfMonth } from 'date-fns'
import api from '../services/api'
import { Calendar, CheckCircle, Clock, WalletCards } from 'lucide-react'
import { translateStatus, translatePaymentMethod } from '../utils/translations'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'
import MonthSelector from '../components/MonthSelector'

const formatCurrency = (value: number) =>
  value.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })

export default function Payments() {
  const [selectedMonth, setSelectedMonth] = useState(startOfMonth(new Date()))

  const monthRange = useMemo(() => ({
    from: format(startOfMonth(selectedMonth), 'yyyy-MM-dd'),
    to: format(endOfMonth(selectedMonth), 'yyyy-MM-dd'),
  }), [selectedMonth])

  const { data: payments = [], isLoading } = useQuery({
    queryKey: ['payments', monthRange],
    queryFn: async () => {
      const params = new URLSearchParams({
        from_date: monthRange.from,
        to_date: monthRange.to,
      })
      const response = await api.get(`/payments?${params.toString()}`)
      return response.data
    },
  })

  const summary = useMemo(() => {
    const executed = payments.filter((payment: any) => payment.status === 'executed')
    const scheduled = payments.filter((payment: any) => payment.status === 'scheduled')
    const total = payments.reduce((sum: number, payment: any) => sum + (payment.amount || 0), 0)
    const paid = executed.reduce((sum: number, payment: any) => sum + (payment.amount || 0), 0)
    const pending = scheduled.reduce((sum: number, payment: any) => sum + (payment.amount || 0), 0)

    return { total, paid, pending, executed: executed.length, scheduled: scheduled.length }
  }, [payments])

  if (isLoading) {
    return <LoadingSpinner message="Carregando pagamentos..." />
  }

  return (
    <div className="space-y-5 p-4 pb-20 sm:p-6 sm:pb-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-950 lg:text-3xl">Pagamentos</h1>
          <p className="mt-1 text-sm text-slate-600">
            Pagamentos agendados ou executados dentro do mês selecionado.
          </p>
        </div>
        <MonthSelector value={selectedMonth} onChange={setSelectedMonth} />
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Impacto no mês</p>
          <p className="mt-2 text-xl font-bold text-slate-950">{formatCurrency(summary.total)}</p>
        </div>
        <div className="rounded-lg border border-emerald-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Pagos</p>
          <p className="mt-2 text-xl font-bold text-emerald-700">{formatCurrency(summary.paid)}</p>
          <p className="mt-1 text-xs text-slate-500">{summary.executed} pagamento(s)</p>
        </div>
        <div className="rounded-lg border border-amber-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Agendados</p>
          <p className="mt-2 text-xl font-bold text-amber-700">{formatCurrency(summary.pending)}</p>
          <p className="mt-1 text-xs text-slate-500">{summary.scheduled} pagamento(s)</p>
        </div>
      </div>

      {payments.length > 0 ? (
        <div className="space-y-3">
          {payments.map((payment: any) => (
            <div
              key={payment.id}
              className="flex flex-col gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition-colors hover:bg-slate-50 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="flex items-start gap-3">
                <div className={`rounded-lg p-2 ${
                  payment.status === 'executed'
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'bg-amber-50 text-amber-700'
                }`}>
                  {payment.status === 'executed' ? (
                    <CheckCircle className="h-5 w-5" />
                  ) : (
                    <Clock className="h-5 w-5" />
                  )}
                </div>
                <div>
                  <p className="text-lg font-bold text-slate-950">{formatCurrency(payment.amount || 0)}</p>
                  <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-600">
                    <span>
                      Vencimento:{' '}
                      <strong className="font-semibold text-slate-900">
                        {payment.scheduled_date
                          ? new Date(payment.scheduled_date).toLocaleDateString('pt-BR')
                          : 'N/A'}
                      </strong>
                    </span>
                    {payment.executed_date && (
                      <span>
                        Pago em:{' '}
                        <strong className="font-semibold text-slate-900">
                          {new Date(payment.executed_date).toLocaleDateString('pt-BR')}
                        </strong>
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between gap-3 sm:flex-col sm:items-end">
                <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${
                  payment.status === 'executed'
                    ? 'bg-emerald-50 text-emerald-700'
                    : payment.status === 'scheduled'
                      ? 'bg-blue-50 text-blue-700'
                      : 'bg-amber-50 text-amber-700'
                }`}>
                  {translateStatus(payment.status)}
                </span>
                <span className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500">
                  <WalletCards className="h-3.5 w-3.5" />
                  {translatePaymentMethod(payment.method)}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={Calendar}
          title="Nenhum pagamento neste mês"
          description="Quando uma despesa for marcada como paga ou agendada, ela aparece aqui associada ao mês selecionado."
        />
      )}
    </div>
  )
}
