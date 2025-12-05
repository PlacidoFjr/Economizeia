import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { Plus, FileText, Upload, Filter, X, Search, Trash2 } from 'lucide-react'
import { translateStatus, translateCategory } from '../utils/translations'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'
import Breadcrumbs from '../components/Breadcrumbs'

const CATEGORIES = [
  { value: '', label: 'Todas as categorias' },
  { value: 'alimentacao', label: 'Alimentação' },
  { value: 'moradia', label: 'Moradia' },
  { value: 'servicos', label: 'Serviços' },
  { value: 'transporte', label: 'Transporte' },
  { value: 'saude', label: 'Saúde' },
  { value: 'investimentos', label: 'Investimentos' },
  { value: 'outras', label: 'Outras' },
]

const STATUS_FILTERS = [
  { value: '', label: 'Todos os status' },
  { value: 'pending', label: 'Pendente' },
  { value: 'confirmed', label: 'Confirmado' },
  { value: 'scheduled', label: 'Agendado' },
  { value: 'paid', label: 'Pago' },
  { value: 'overdue', label: 'Vencido' },
]

export default function Bills() {
  const [filters, setFilters] = useState({
    category: '',
    status: '',
    issuer: '',
    from_date: '',
    to_date: '',
  })
  const [showFilters, setShowFilters] = useState(false)
  const queryClient = useQueryClient()
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const deleteMutation = useMutation({
    mutationFn: async (billId: string) => {
      await api.delete(`/bills/${billId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bills'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  const handleDelete = async (billId: string, issuer: string) => {
    if (!confirm(`Deseja realmente excluir o boleto "${issuer}"?`)) {
      return
    }
    setDeletingId(billId)
    try {
      await deleteMutation.mutateAsync(billId)
    } catch (error) {
      console.error('Erro ao deletar:', error)
    } finally {
      setDeletingId(null)
    }
  }

  const { data: bills, isLoading } = useQuery({
    queryKey: ['bills', filters],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (filters.category) params.append('category', filters.category)
      if (filters.status) params.append('status', filters.status)
      if (filters.issuer) params.append('issuer', filters.issuer)
      if (filters.from_date) params.append('from_date', filters.from_date)
      if (filters.to_date) params.append('to_date', filters.to_date)
      
      params.append('is_bill', 'true') // Apenas boletos
      const response = await api.get(`/bills?${params.toString()}`)
      return response.data
    },
  })

  const clearFilters = () => {
    setFilters({
      category: '',
      status: '',
      issuer: '',
      from_date: '',
      to_date: '',
    })
  }

  const hasActiveFilters = Object.values(filters).some(v => v !== '')

  if (isLoading) {
    return <LoadingSpinner message="Carregando boletos..." />
  }

  return (
    <div className="space-y-6 p-4 sm:p-6">
      <Breadcrumbs items={[{ label: 'Meus Boletos' }]} />
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div className="flex-1">
          <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900 mb-1">Meus Boletos</h1>
          <p className="text-xs sm:text-sm text-gray-600">Gerencie todos os seus boletos e faturas</p>
        </div>
        <div className="flex flex-wrap gap-2 sm:gap-3 w-full sm:w-auto">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center px-3 sm:px-4 py-2 border rounded-md font-semibold text-xs sm:text-sm transition-colors ${
              showFilters || hasActiveFilters
                ? 'bg-gray-900 text-white border-gray-900 hover:bg-gray-800'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            <Filter className="w-4 h-4 mr-1 sm:mr-2" />
            <span className="hidden sm:inline">Filtros</span>
            <span className="sm:hidden">Filtro</span>
            {hasActiveFilters && (
              <span className="ml-1 sm:ml-2 bg-white text-gray-900 rounded-full px-1.5 sm:px-2 py-0.5 text-xs">
                {Object.values(filters).filter(v => v !== '').length}
              </span>
            )}
          </button>
          <Link
            to="/app/bills/add"
            className="flex items-center px-3 sm:px-4 py-2 bg-gray-900 text-white rounded-md hover:bg-gray-800 font-semibold text-xs sm:text-sm transition-colors whitespace-nowrap"
          >
            <Plus className="w-4 h-4 mr-1 sm:mr-2" />
            <span className="hidden sm:inline">Adicionar Despesa</span>
            <span className="sm:hidden">Adicionar</span>
          </Link>
          <Link
            to="/app/bills/upload"
            className="flex items-center px-3 sm:px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 font-semibold text-xs sm:text-sm transition-colors whitespace-nowrap"
          >
            <Upload className="w-4 h-4 mr-1 sm:mr-2" />
            Upload
          </Link>
        </div>
      </div>

      {/* Filtros */}
      {showFilters && (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
            {/* Categoria */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Categoria</label>
              <select
                value={filters.category}
                onChange={(e) => setFilters({ ...filters, category: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Status */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Status</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                {STATUS_FILTERS.map((status) => (
                  <option key={status.value} value={status.value}>
                    {status.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Emissor */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Emissor</label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={filters.issuer}
                  onChange={(e) => setFilters({ ...filters, issuer: e.target.value })}
                  placeholder="Buscar emissor..."
                  className="w-full pl-8 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
                />
              </div>
            </div>

            {/* Data Inicial */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">De</label>
              <input
                type="date"
                value={filters.from_date}
                onChange={(e) => setFilters({ ...filters, from_date: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
              />
            </div>

            {/* Data Final */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Até</label>
              <input
                type="date"
                value={filters.to_date}
                onChange={(e) => setFilters({ ...filters, to_date: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
              />
            </div>
          </div>

          {hasActiveFilters && (
            <div className="mt-4 flex justify-end">
              <button
                onClick={clearFilters}
                className="flex items-center px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                <X className="w-4 h-4 mr-1" />
                Limpar Filtros
              </button>
            </div>
          )}
        </div>
      )}

      {bills && bills.length > 0 ? (
        <>
          {/* Tabela Desktop */}
          <div className="hidden lg:block bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                    Emissor
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                    Valor
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                    Vencimento
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                    Categoria
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                    Confiança
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {bills.map((bill: any) => (
                  <tr key={bill.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="bg-gray-100 p-1.5 rounded mr-2">
                          <FileText className="w-4 h-4 text-gray-600" />
                        </div>
                        <div className="text-sm font-medium text-gray-900">
                          {bill.issuer || 'Desconhecido'}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-semibold text-gray-900">R$ {bill.amount?.toFixed(2) || '0.00'}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-700">
                        {bill.due_date ? new Date(bill.due_date).toLocaleDateString('pt-BR') : 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 inline-flex text-xs font-medium rounded bg-gray-100 text-gray-700">
                        {bill.category ? translateCategory(bill.category) : 'Sem categoria'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 inline-flex text-xs font-semibold rounded ${
                        bill.status === 'paid' ? 'bg-green-100 text-green-800' :
                        bill.status === 'overdue' ? 'bg-red-100 text-red-800' :
                        bill.status === 'scheduled' ? 'bg-blue-100 text-blue-800' :
                        bill.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {translateStatus(bill.status)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-12 bg-gray-200 rounded-full h-2 mr-2">
                          <div 
                            className={`h-2 rounded-full ${
                              bill.confidence >= 0.9 ? 'bg-green-600' :
                              bill.confidence >= 0.7 ? 'bg-yellow-600' :
                              'bg-red-600'
                            }`}
                            style={{ width: `${(bill.confidence * 100)}%` }}
                          ></div>
                        </div>
                        <span className="text-xs font-medium text-gray-700">
                          {(bill.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center space-x-3">
                        <Link
                          to={`/app/bills/${bill.id}`}
                          className="text-gray-700 hover:text-gray-900 hover:underline text-sm font-medium"
                          aria-label={`Ver detalhes do boleto ${bill.issuer || ''}`}
                        >
                          Ver detalhes
                        </Link>
                        <button
                          onClick={() => handleDelete(bill.id, bill.issuer || 'Boleto')}
                          disabled={deletingId === bill.id}
                          className="text-red-600 hover:text-red-800 disabled:opacity-50 p-1 rounded hover:bg-red-50 transition-colors min-w-[32px] min-h-[32px] flex items-center justify-center"
                          title="Excluir boleto"
                          aria-label={`Excluir boleto ${bill.issuer || ''}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        
        {/* Cards Mobile */}
        <div className="lg:hidden space-y-4">
          {bills.map((bill: any) => (
            <div key={bill.id} className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <div className="bg-gray-100 p-1.5 rounded mr-2">
                      <FileText className="w-4 h-4 text-gray-600" />
                    </div>
                    <h3 className="text-base font-semibold text-gray-900">
                      {bill.issuer || 'Desconhecido'}
                    </h3>
                  </div>
                  <p className="text-lg font-bold text-gray-900 mb-1">
                    R$ {bill.amount?.toFixed(2) || '0.00'}
                  </p>
                  <p className="text-sm text-gray-600">
                    Vencimento: {bill.due_date ? new Date(bill.due_date).toLocaleDateString('pt-BR') : 'N/A'}
                  </p>
                </div>
                <span className={`px-2 py-1 inline-flex text-xs font-semibold rounded ${
                  bill.status === 'paid' ? 'bg-green-100 text-green-800' :
                  bill.status === 'overdue' ? 'bg-red-100 text-red-800' :
                  bill.status === 'scheduled' ? 'bg-blue-100 text-blue-800' :
                  bill.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {translateStatus(bill.status)}
                </span>
              </div>
              
              <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                <div className="flex items-center space-x-3">
                  {bill.category && (
                    <span className="px-2 py-1 text-xs font-medium rounded bg-gray-100 text-gray-700">
                      {translateCategory(bill.category)}
                    </span>
                  )}
                  <div className="flex items-center">
                    <div className="w-10 bg-gray-200 rounded-full h-1.5 mr-1.5">
                      <div 
                        className={`h-1.5 rounded-full ${
                          bill.confidence >= 0.9 ? 'bg-green-600' :
                          bill.confidence >= 0.7 ? 'bg-yellow-600' :
                          'bg-red-600'
                        }`}
                        style={{ width: `${(bill.confidence * 100)}%` }}
                      ></div>
                    </div>
                    <span className="text-xs text-gray-600">
                      {(bill.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <Link
                    to={`/app/bills/${bill.id}`}
                    className="text-sm font-medium text-gray-700 hover:text-gray-900 hover:underline"
                    aria-label={`Ver detalhes do boleto ${bill.issuer || ''}`}
                  >
                    Ver →
                  </Link>
                  <button
                    onClick={() => handleDelete(bill.id, bill.issuer || 'Boleto')}
                    disabled={deletingId === bill.id}
                    className="text-red-600 hover:text-red-800 disabled:opacity-50 p-2 rounded hover:bg-red-50 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
                    title="Excluir"
                    aria-label={`Excluir boleto ${bill.issuer || ''}`}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </>
      ) : (
        <EmptyState
          icon={FileText}
          title="Nenhum boleto encontrado"
          description="Comece fazendo upload do seu primeiro boleto para ter controle total dos seus pagamentos."
          action={{
            label: "Fazer Upload do Primeiro Boleto",
            onClick: () => window.location.href = '/app/bills/upload',
            icon: Upload
          }}
        />
      )}
    </div>
  )
}

