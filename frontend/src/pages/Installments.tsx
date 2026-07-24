import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { endOfMonth, isWithinInterval, parseISO, startOfMonth } from 'date-fns'
import api from '../services/api'
import { CalendarDays, CreditCard, Plus } from 'lucide-react'
import { translateStatus } from '../utils/translations'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'
import MonthSelector from '../components/MonthSelector'

interface InstallmentGroup {
  issuer: string
  totalAmount: number
  monthAmount: number
  totalInstallments: number
  paidInstallments: number
  remainingInstallments: number
  nextDueDate: string | null
  monthItems: any[]
  allItems: any[]
}

const formatCurrency = (value: number) =>
  value.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })

const parseBillDate = (bill: any) => {
  if (!bill.due_date) return null
  try {
    return parseISO(bill.due_date)
  } catch {
    return null
  }
}

export default function Installments() {
  const [selectedMonth, setSelectedMonth] = useState(startOfMonth(new Date()))

  const monthInterval = useMemo(() => ({
    start: startOfMonth(selectedMonth),
    end: endOfMonth(selectedMonth),
  }), [selectedMonth])

  const { data: bills = [], isLoading } = useQuery({
    queryKey: ['installment-bills'],
    queryFn: async () => {
      const response = await api.get('/bills?is_bill=false')
      return response.data
    },
  })

  const installmentGroups: InstallmentGroup[] = useMemo(() => {
    const grouped: Record<string, any[]> = {}

    bills
      .filter((bill: any) => bill.type === 'expense')
      .forEach((bill: any) => {
        const issuer = bill.issuer || 'Desconhecido'
        if (!grouped[issuer]) grouped[issuer] = []
        grouped[issuer].push(bill)
      })

    return Object.entries(grouped)
      .map(([issuer, issuerBills]) => {
        const allItems = [...issuerBills].sort((a: any, b: any) =>
          new Date(a.due_date || 0).getTime() - new Date(b.due_date || 0).getTime()
        )
        const monthItems = allItems.filter((bill: any) => {
          const date = parseBillDate(bill)
          return date ? isWithinInterval(date, monthInterval) : false
        })
        const pendingItems = allItems.filter((bill: any) => bill.status !== 'paid')
        const nextDueDate = pendingItems[0]?.due_date || null

        return {
          issuer,
          totalAmount: allItems.reduce((sum, bill) => sum + (bill.amount || 0), 0),
          monthAmount: monthItems.reduce((sum, bill) => sum + (bill.amount || 0), 0),
          totalInstallments: allItems.length,
          paidInstallments: allItems.filter((bill: any) => bill.status === 'paid').length,
          remainingInstallments: pendingItems.length,
          nextDueDate,
          monthItems,
          allItems,
        }
      })
      .filter((group) => group.totalInstallments > 1 && group.monthItems.length > 0)
      .sort((a, b) => b.monthAmount - a.monthAmount)
  }, [bills, monthInterval])

  const monthTotal = useMemo(
    () => installmentGroups.reduce((sum, group) => sum + group.monthAmount, 0),
    [installmentGroups]
  )

  if (isLoading) {
    return <LoadingSpinner message="Carregando parcelados..." />
  }

  return (
    <div className="space-y-5 p-4 pb-20 sm:p-6 sm:pb-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-950 lg:text-3xl">Parcelados</h1>
          <p className="mt-1 text-sm text-slate-600">
            Compras repetidas do mesmo emissor, com o impacto no mês selecionado.
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <MonthSelector value={selectedMonth} onChange={setSelectedMonth} />
          <Link
            to="/app/transactions/add"
            className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-slate-950 px-4 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-slate-800"
          >
            <Plus className="h-4 w-4" />
            Adicionar
          </Link>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Impacto no mês</p>
          <p className="mt-2 text-xl font-bold text-slate-950">{formatCurrency(monthTotal)}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Grupos ativos</p>
          <p className="mt-2 text-xl font-bold text-slate-950">{installmentGroups.length}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Parcelas no mês</p>
          <p className="mt-2 text-xl font-bold text-slate-950">
            {installmentGroups.reduce((sum, group) => sum + group.monthItems.length, 0)}
          </p>
        </div>
      </div>

      {installmentGroups.length > 0 ? (
        <div className="space-y-4">
          {installmentGroups.map((group) => (
            <div key={group.issuer} className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
              <div className="border-b border-slate-200 bg-slate-50 p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h3 className="text-base font-bold text-slate-950">{group.issuer}</h3>
                    <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600">
                      <span>Total: <strong className="text-slate-950">{formatCurrency(group.totalAmount)}</strong></span>
                      <span>Parcelas: <strong className="text-slate-950">{group.totalInstallments}x</strong></span>
                      <span>
                        Pagas: <strong className="text-slate-950">{group.paidInstallments}</strong>
                      </span>
                      <span className={group.remainingInstallments > 0 ? 'text-amber-700' : 'text-emerald-700'}>
                        {group.remainingInstallments > 0 ? `${group.remainingInstallments} restantes` : 'Quitado'}
                      </span>
                    </div>
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-left sm:text-right">
                    <p className="text-xs font-semibold text-slate-500">Neste mês</p>
                    <p className="text-base font-bold text-slate-950">{formatCurrency(group.monthAmount)}</p>
                  </div>
                </div>
              </div>

              <div className="space-y-2 p-4">
                {group.monthItems.map((bill: any) => {
                  const billIndex = group.allItems.findIndex((item) => item.id === bill.id)
                  return (
                    <div
                      key={bill.id}
                      className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-3 transition-colors hover:bg-slate-50 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div className="flex items-start gap-3">
                        <div className={`rounded-lg p-2 ${
                          bill.status === 'paid'
                            ? 'bg-emerald-50 text-emerald-700'
                            : bill.status === 'overdue'
                              ? 'bg-red-50 text-red-700'
                              : 'bg-amber-50 text-amber-700'
                        }`}>
                          <CreditCard className="h-4 w-4" />
                        </div>
                        <div>
                          <p className="text-sm font-bold text-slate-950">
                            Parcela {billIndex + 1} de {group.totalInstallments}
                          </p>
                          <p className="mt-1 inline-flex items-center gap-1 text-xs text-slate-600">
                            <CalendarDays className="h-3.5 w-3.5" />
                            {bill.due_date ? new Date(bill.due_date).toLocaleDateString('pt-BR') : 'N/A'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between gap-3 sm:flex-col sm:items-end">
                        <p className="text-sm font-bold text-slate-950">{formatCurrency(bill.amount || 0)}</p>
                        <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${
                          bill.status === 'paid' ? 'bg-emerald-50 text-emerald-700' :
                          bill.status === 'overdue' ? 'bg-red-50 text-red-700' :
                          bill.status === 'scheduled' ? 'bg-blue-50 text-blue-700' :
                          'bg-amber-50 text-amber-700'
                        }`}>
                          {translateStatus(bill.status)}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={CreditCard}
          title="Nenhum parcelado neste mês"
          description="Parcelados aparecem quando há mais de uma despesa do mesmo emissor e ao menos uma parcela vence no mês selecionado."
          action={{
            label: 'Adicionar despesa',
            onClick: () => { window.location.href = '/app/transactions/add' },
            icon: Plus,
          }}
        />
      )}
    </div>
  )
}
