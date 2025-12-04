import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import api from '../services/api'
import { useState } from 'react'
import { Check, X, Calendar, DollarSign, ArrowLeft, FileText } from 'lucide-react'
import { translateStatus } from '../utils/translations'

export default function BillDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [showSchedule, setShowSchedule] = useState(false)
  const [scheduledDate, setScheduledDate] = useState('')
  const [notifyDays] = useState([7, 3, 1])

  const { data: bill, isLoading } = useQuery({
    queryKey: ['bill', id],
    queryFn: async () => {
      const response = await api.get(`/bills/${id}`)
      return response.data
    },
  })

  const confirmMutation = useMutation({
    mutationFn: async (confirm: boolean) => {
      const response = await api.post(`/bills/${id}/confirm`, {
        confirm,
        corrections: {},
      })
      return response.data
    },
    onSuccess: () => {
      window.location.reload()
    },
  })

  const scheduleMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post(`/bills/${id}/schedule`, data)
      return response.data
    },
    onSuccess: () => {
      navigate('/payments')
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-3"></div>
          <p className="text-sm text-gray-600">Carregando detalhes...</p>
        </div>
      </div>
    )
  }

  if (!bill) {
    return (
      <div className="text-center py-12">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
          <FileText className="w-12 h-12 text-red-400 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-red-900 mb-1">Boleto não encontrado</h3>
          <p className="text-sm text-red-700 mb-4">O boleto solicitado não existe ou foi removido.</p>
          <button
            onClick={() => navigate('/bills')}
            className="px-4 py-2 bg-gray-900 text-white rounded-md hover:bg-gray-800 font-semibold text-sm transition-colors"
          >
            Voltar para Boletos
          </button>
        </div>
      </div>
    )
  }

  const requiresReview = bill.confidence < 0.9

  return (
    <div className="max-w-4xl mx-auto space-y-4 p-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Detalhes do Boleto</h1>
        <button
          onClick={() => navigate('/bills')}
          className="flex items-center px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md font-medium text-sm transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          Voltar
        </button>
      </div>

      {requiresReview && bill.status === 'pending' && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <div className="flex items-center">
            <div className="bg-yellow-100 p-1.5 rounded mr-2">
              <X className="w-4 h-4 text-yellow-600" />
            </div>
            <div>
              <p className="font-semibold text-sm text-yellow-900">Atenção: Revisão Manual Necessária</p>
              <p className="text-xs text-yellow-700 mt-0.5">
                Confiança da extração: <span className="font-semibold">{(bill.confidence * 100).toFixed(0)}%</span>
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1 block">Emissor</label>
            <p className="text-base font-semibold text-gray-900">{bill.issuer || 'Não identificado'}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1 block">Valor</label>
            <p className="text-base font-semibold text-gray-900 flex items-center">
              <DollarSign className="w-4 h-4 mr-1" />
              R$ {bill.amount?.toFixed(2) || '0.00'}
            </p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1 block">Vencimento</label>
            <p className="text-base font-semibold text-gray-900 flex items-center">
              <Calendar className="w-4 h-4 mr-1" />
              {bill.due_date ? new Date(bill.due_date).toLocaleDateString('pt-BR') : 'N/A'}
            </p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1 block">Status</label>
            <p className="text-sm font-semibold">
              <span className={`px-2 py-1 rounded text-xs font-semibold ${
                bill.status === 'paid' ? 'bg-green-100 text-green-800' :
                bill.status === 'overdue' ? 'bg-red-100 text-red-800' :
                bill.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                bill.status === 'scheduled' ? 'bg-blue-100 text-blue-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {translateStatus(bill.status)}
              </span>
            </p>
          </div>
        </div>

        {bill.barcode && (
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2 block">Código de Barras</label>
            <p className="text-xs font-mono bg-white p-3 rounded border border-gray-300 text-gray-900 break-all">{bill.barcode}</p>
          </div>
        )}

        {bill.extracted_json && (
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2 block">Dados Extraídos (JSON)</label>
            <pre className="text-xs bg-white p-3 rounded border border-gray-300 overflow-auto max-h-96 text-gray-900">
              {JSON.stringify(bill.extracted_json, null, 2)}
            </pre>
          </div>
        )}

        {bill.status === 'pending' && (
          <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-gray-200">
            <button
              onClick={() => confirmMutation.mutate(true)}
              disabled={confirmMutation.isPending}
              className="flex-1 flex items-center justify-center px-4 py-2 bg-gray-900 text-white rounded-md hover:bg-gray-800 disabled:opacity-50 font-semibold text-sm transition-colors"
            >
              <Check className="w-4 h-4 mr-2" />
              {confirmMutation.isPending ? 'Confirmando...' : 'Confirmar Boleto'}
            </button>
            <button
              onClick={() => confirmMutation.mutate(false)}
              disabled={confirmMutation.isPending}
              className="flex-1 flex items-center justify-center px-4 py-2 bg-gray-100 text-gray-900 rounded-md hover:bg-gray-200 disabled:opacity-50 font-semibold text-sm transition-colors"
            >
              <X className="w-4 h-4 mr-2" />
              Cancelar
            </button>
          </div>
        )}

        {bill.status === 'confirmed' && !showSchedule && (
          <button
            onClick={() => setShowSchedule(true)}
            className="w-full py-2 px-4 bg-gray-900 text-white rounded-md hover:bg-gray-800 font-semibold text-sm transition-colors flex items-center justify-center"
          >
            <Calendar className="w-4 h-4 mr-2" />
            Agendar Pagamento
          </button>
        )}

        {showSchedule && (
          <div className="space-y-4 pt-4 border-t border-gray-200 bg-gray-50 p-4 rounded-lg">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">
              Agendar Pagamento
            </h3>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Data do Pagamento
              </label>
              <input
                type="date"
                value={scheduledDate}
                onChange={(e) => setScheduledDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:border-gray-500 focus:ring-2 focus:ring-gray-200 text-sm"
                min={new Date().toISOString().split('T')[0]}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Método de Pagamento
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:border-gray-500 focus:ring-2 focus:ring-gray-200 text-sm bg-white">
                <option value="PIX">PIX</option>
                <option value="BOLETO">Boleto</option>
                <option value="DEBIT">Débito Automático</option>
                <option value="CREDIT">Cartão de Crédito</option>
                <option value="TRANSFER">Transferência Bancária</option>
              </select>
            </div>
            <button
              onClick={() => {
                scheduleMutation.mutate({
                  scheduled_date: scheduledDate,
                  method: 'PIX',
                  notify_before_days: notifyDays,
                })
              }}
              disabled={!scheduledDate || scheduleMutation.isPending}
              className="w-full py-2 px-4 bg-gray-900 text-white rounded-md hover:bg-gray-800 disabled:opacity-50 font-semibold text-sm transition-colors"
            >
              {scheduleMutation.isPending ? 'Agendando...' : 'Confirmar Agendamento'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

