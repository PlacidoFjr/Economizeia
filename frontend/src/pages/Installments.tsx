import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import { Plus, CreditCard } from 'lucide-react'
import { useState } from 'react'
import { translateStatus } from '../utils/translations'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'

interface InstallmentGroup {
  issuer: string
  total_amount: number
  total_installments: number
  paid_installments: number
  remaining_installments: number
  next_due_date: string | null
  bills: any[]
}

export default function Installments() {
  const [showCreateForm, setShowCreateForm] = useState(false)

  const { data: bills, isLoading } = useQuery({
    queryKey: ['bills'],
    queryFn: async () => {
      const response = await api.get('/bills')
      return response.data
    },
  })

  // Agrupar boletos por emissor e identificar parcelados - memoizado
  const installmentGroups: InstallmentGroup[] = useMemo(() => {
    const groups: InstallmentGroup[] = []
    if (!bills) return groups

    const grouped: { [key: string]: any[] } = {}
    
    bills.forEach((bill: any) => {
      const issuer = bill.issuer || 'Desconhecido'
      if (!grouped[issuer]) {
        grouped[issuer] = []
      }
      grouped[issuer].push(bill)
    })

    Object.entries(grouped).forEach(([issuer, issuerBills]) => {
      // Verificar se há múltiplos boletos do mesmo emissor (possível parcelado)
      if (issuerBills.length > 1) {
        const totalAmount = issuerBills.reduce((sum, b) => sum + (b.amount || 0), 0)
        const paidBills = issuerBills.filter((b: any) => b.status === 'paid')
        const pendingBills = issuerBills.filter((b: any) => b.status !== 'paid')
        
        const nextDue = pendingBills.length > 0 
          ? pendingBills.sort((a: any, b: any) => 
              new Date(a.due_date || 0).getTime() - new Date(b.due_date || 0).getTime()
            )[0]?.due_date
          : null

        groups.push({
          issuer,
          total_amount: totalAmount,
          total_installments: issuerBills.length,
          paid_installments: paidBills.length,
          remaining_installments: pendingBills.length,
          next_due_date: nextDue,
          bills: issuerBills.sort((a: any, b: any) => 
            new Date(a.due_date || 0).getTime() - new Date(b.due_date || 0).getTime()
          )
        })
      }
    })
    
    return groups
  }, [bills])

  if (isLoading) {
    return <LoadingSpinner message="Carregando parcelados..." />
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 mb-1">Parcelados</h1>
          <p className="text-sm text-gray-600">Gerencie suas compras parceladas e financiamentos</p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex items-center px-4 py-2 bg-gray-900 text-white rounded-md hover:bg-gray-800 font-semibold text-sm transition-colors"
        >
          <Plus className="w-4 h-4 mr-2" />
          Novo Parcelado
        </button>
      </div>

      {showCreateForm && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Criar Novo Parcelado</h3>
          <p className="text-sm text-gray-600 mb-4">
            Para criar um parcelado, use o chatbot ou faça upload dos boletos. 
            O sistema identificará automaticamente quando há múltiplos boletos do mesmo emissor.
          </p>
          <button
            onClick={() => setShowCreateForm(false)}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 font-medium text-sm transition-colors"
          >
            Fechar
          </button>
        </div>
      )}

      {installmentGroups.length > 0 ? (
        <div className="space-y-4">
          {installmentGroups.map((group, index) => (
            <div key={index} className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              {/* Header do Grupo */}
              <div className="bg-gray-50 border-b border-gray-200 p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-base font-semibold text-gray-900 mb-1">{group.issuer}</h3>
                    <div className="flex items-center space-x-4 text-xs text-gray-600">
                      <span>Total: <strong className="text-gray-900">R$ {group.total_amount.toFixed(2)}</strong></span>
                      <span>Parcelas: <strong className="text-gray-900">{group.total_installments}x</strong></span>
                      <span className={`${group.remaining_installments > 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {group.remaining_installments > 0 
                          ? `${group.remaining_installments} restantes`
                          : 'Quitado'}
                      </span>
                    </div>
                  </div>
                  {group.next_due_date && (
                    <div className="text-right">
                      <p className="text-xs text-gray-600">Próximo vencimento</p>
                      <p className="text-sm font-semibold text-gray-900">
                        {new Date(group.next_due_date).toLocaleDateString('pt-BR')}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Lista de Parcelas */}
              <div className="p-4">
                <div className="space-y-2">
                  {group.bills.map((bill: any, billIndex: number) => (
                    <div
                      key={bill.id}
                      className="flex justify-between items-center p-3 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <div className={`p-1.5 rounded ${
                          bill.status === 'paid' 
                            ? 'bg-green-100' 
                            : bill.status === 'overdue'
                            ? 'bg-red-100'
                            : 'bg-yellow-100'
                        }`}>
                          <CreditCard className={`w-4 h-4 ${
                            bill.status === 'paid' 
                              ? 'text-green-600' 
                              : bill.status === 'overdue'
                              ? 'text-red-600'
                              : 'text-yellow-600'
                          }`} />
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-gray-900">
                            Parcela {billIndex + 1} de {group.total_installments}
                          </p>
                          <p className="text-xs text-gray-600">
                            Vencimento: {bill.due_date ? new Date(bill.due_date).toLocaleDateString('pt-BR') : 'N/A'}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-gray-900 mb-1">
                          R$ {bill.amount?.toFixed(2) || '0.00'}
                        </p>
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                          bill.status === 'paid' ? 'bg-green-100 text-green-800' :
                          bill.status === 'overdue' ? 'bg-red-100 text-red-800' :
                          bill.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                          bill.status === 'scheduled' ? 'bg-blue-100 text-blue-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {translateStatus(bill.status)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={CreditCard}
          title="Nenhum parcelado encontrado"
          description="Parcelados são identificados automaticamente quando há múltiplos boletos do mesmo emissor."
          action={{
            label: "Fazer Upload de Boletos",
            onClick: () => window.location.href = '/app/bills/upload',
            icon: Plus
          }}
        />
      )}
    </div>
  )
}

