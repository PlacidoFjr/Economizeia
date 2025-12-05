import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import { Calendar, CheckCircle, Clock } from 'lucide-react'
import { translateStatus, translatePaymentMethod } from '../utils/translations'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'

export default function Payments() {
  const { data: payments, isLoading } = useQuery({
    queryKey: ['payments'],
    queryFn: async () => {
      const response = await api.get('/payments')
      return response.data
    },
  })

  if (isLoading) {
    return <LoadingSpinner message="Carregando pagamentos..." />
  }

  return (
    <div className="space-y-6 p-6">
      <div className="mb-6">
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 mb-1">Pagamentos</h1>
        <p className="text-sm text-gray-600">Acompanhe seus pagamentos agendados e executados</p>
      </div>

      {payments && payments.length > 0 ? (
        <div className="space-y-3">
          {payments.map((payment: any) => (
            <div
              key={payment.id}
              className="bg-white rounded-lg border border-gray-200 p-4 flex justify-between items-center hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center space-x-4">
                <div className={`p-2 rounded ${
                  payment.status === 'executed' 
                    ? 'bg-green-100' 
                    : 'bg-yellow-100'
                }`}>
                  {payment.status === 'executed' ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <Clock className="w-5 h-5 text-yellow-600" />
                  )}
                </div>
                <div>
                  <p className="font-semibold text-lg text-gray-900 mb-1">R$ {payment.amount?.toFixed(2) || '0.00'}</p>
                  <div className="flex items-center space-x-3 text-xs">
                    <div>
                      <span className="text-gray-600">Vencimento: </span>
                      <span className="text-gray-900 font-medium">
                        {payment.scheduled_date
                          ? new Date(payment.scheduled_date).toLocaleDateString('pt-BR')
                          : 'N/A'}
                      </span>
                    </div>
                    {payment.executed_date && (
                      <div>
                        <span className="text-gray-600">Executado em: </span>
                        <span className="text-gray-900 font-medium">
                          {new Date(payment.executed_date).toLocaleDateString('pt-BR')}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <span className={`px-2 py-1 rounded text-xs font-semibold mb-1 inline-block ${
                  payment.status === 'executed'
                    ? 'bg-green-100 text-green-800'
                    : payment.status === 'scheduled'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {translateStatus(payment.status)}
                </span>
                <p className="text-xs font-medium text-gray-600 mt-1">
                  {translatePaymentMethod(payment.method)}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={Calendar}
          title="Nenhum pagamento encontrado"
          description="Agende pagamentos para seus boletos e tenha controle total dos seus vencimentos."
        />
      )}
    </div>
  )
}

