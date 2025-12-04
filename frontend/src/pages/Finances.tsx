import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { Plus, DollarSign, Filter, X, Search, Trash2, TrendingUp, TrendingDown } from 'lucide-react'
import { translateStatus } from '../utils/translations'

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

export default function Finances() {
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState({
    category: '',
    status: '',
    issuer: '',
    from_date: '',
    to_date: '',
    type: '', // expense ou income
  })
  const [showFilters, setShowFilters] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const deleteMutation = useMutation({
    mutationFn: async (itemId: string) => {
      await api.delete(`/bills/${itemId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finances'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  const handleDelete = async (itemId: string, issuer: string) => {
    if (!confirm(`Deseja realmente excluir "${issuer}"?`)) {
      return
    }
    setDeletingId(itemId)
    try {
      await deleteMutation.mutateAsync(itemId)
    } catch (error) {
      console.error('Erro ao deletar:', error)
    } finally {
      setDeletingId(null)
    }
  }

  const { data: finances, isLoading } = useQuery({
    queryKey: ['finances', filters],
    queryFn: async () => {
      const params = new URLSearchParams()
      params.append('is_bill', 'false') // Apenas transações não-boletos
      if (filters.category) params.append('category', filters.category)
      if (filters.status) params.append('status', filters.status)
      if (filters.issuer) params.append('issuer', filters.issuer)
      if (filters.from_date) params.append('from_date', filters.from_date)
      if (filters.to_date) params.append('to_date', filters.to_date)
      
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
      type: '',
    })
  }

  const hasActiveFilters = Object.values(filters).some(v => v !== '')

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-3"></div>
          <p className="text-sm text-gray-600">Carregando finanças...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-4 sm:p-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 mb-1">Minhas Finanças</h1>
          <p className="text-sm text-gray-600">Gerencie receitas e despesas (não-boletos)</p>
        </div>
        <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-3 mt-4 sm:mt-0 w-full sm:w-auto">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center justify-center w-full sm:w-auto px-4 py-2 border rounded-md font-semibold text-sm transition-colors ${
              showFilters || hasActiveFilters
                ? 'bg-gray-900 text-white border-gray-900 hover:bg-gray-800'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            <Filter className="w-4 h-4 mr-2" />
            Filtros
            {hasActiveFilters && (
              <span className="ml-2 bg-white text-gray-900 rounded-full px-2 py-0.5 text-xs">
                {Object.values(filters).filter(v => v !== '').length}
              </span>
            )}
          </button>
          <Link
            to="/bills/add"
            className="flex items-center justify-center w-full sm:w-auto px-4 py-2 bg-gray-900 text-white rounded-md hover:bg-gray-800 font-semibold text-sm transition-colors"
          >
            <Plus className="w-4 h-4 mr-2" />
            Adicionar Transação
          </Link>
        </div>
      </div>

      {/* Filtros */}
      {showFilters && (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
            {/* Tipo */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Tipo</label>
              <select
                value={filters.type}
                onChange={(e) => setFilters({ ...filters, type: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                <option value="">Todos</option>
                <option value="expense">Despesa</option>
                <option value="income">Receita</option>
              </select>
            </div>

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
              <label className="block text-xs font-semibold text-gray-700 mb-1">Fonte/Emissor</label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={filters.issuer}
                  onChange={(e) => setFilters({ ...filters, issuer: e.target.value })}
                  placeholder="Buscar..."
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

      {finances && finances.length > 0 ? (
        <>
          {/* Tabela Desktop */}
          <div className="hidden lg:block bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                      Fonte/Emissor
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                      Valor
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                      Data
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                      Categoria
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-200">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {finances.map((item: any) => (
                    <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {item.type === 'income' ? (
                            <TrendingUp className="w-4 h-4 text-green-600 mr-2" />
                          ) : (
                            <TrendingDown className="w-4 h-4 text-red-600 mr-2" />
                          )}
                          <span className="text-sm font-medium text-gray-900">
                            {item.type === 'income' ? 'Receita' : 'Despesa'}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {item.issuer || 'Desconhecido'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`text-sm font-semibold ${
                          item.type === 'income' ? 'text-green-700' : 'text-red-700'
                        }`}>
                          {item.type === 'income' ? '+' : '-'} R$ {item.amount?.toFixed(2) || '0.00'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-gray-700">
                          {item.due_date ? new Date(item.due_date).toLocaleDateString('pt-BR') : 'N/A'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-1 inline-flex text-xs font-medium rounded bg-gray-100 text-gray-700">
                          {item.category ? CATEGORIES.find(c => c.value === item.category)?.label || item.category : 'Sem categoria'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 inline-flex text-xs font-semibold rounded ${
                          item.status === 'paid' ? 'bg-green-100 text-green-800' :
                          item.status === 'overdue' ? 'bg-red-100 text-red-800' :
                          item.status === 'scheduled' ? 'bg-blue-100 text-blue-800' :
                          item.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {translateStatus(item.status)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => handleDelete(item.id, item.issuer || 'Item')}
                          disabled={deletingId === item.id}
                          className="text-red-600 hover:text-red-800 disabled:opacity-50 flex items-center"
                          title="Excluir"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          
          {/* Cards Mobile */}
          <div className="lg:hidden space-y-4">
            {finances.map((item: any) => (
              <div key={item.id} className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <div className={`p-1.5 rounded mr-2 ${
                        item.type === 'income' ? 'bg-green-100' : 'bg-red-100'
                      }`}>
                        {item.type === 'income' ? (
                          <TrendingUp className="w-4 h-4 text-green-600" />
                        ) : (
                          <TrendingDown className="w-4 h-4 text-red-600" />
                        )}
                      </div>
                      <h3 className="text-base font-semibold text-gray-900">
                        {item.issuer || 'Desconhecido'}
                      </h3>
                    </div>
                    <p className={`text-lg font-bold mb-1 ${
                      item.type === 'income' ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {item.type === 'income' ? '+' : '-'} R$ {item.amount?.toFixed(2) || '0.00'}
                    </p>
                    <p className="text-sm text-gray-600">
                      {item.type === 'income' ? 'Recebimento' : 'Vencimento'}: {item.due_date ? new Date(item.due_date).toLocaleDateString('pt-BR') : 'N/A'}
                    </p>
                  </div>
                  <span className={`px-2 py-1 inline-flex text-xs font-semibold rounded ${
                    item.status === 'paid' ? 'bg-green-100 text-green-800' :
                    item.status === 'overdue' ? 'bg-red-100 text-red-800' :
                    item.status === 'scheduled' ? 'bg-blue-100 text-blue-800' :
                    item.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {translateStatus(item.status)}
                  </span>
                </div>
                <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                  <div className="flex items-center space-x-3">
                    {item.category && (
                      <span className="px-2 py-1 text-xs font-medium rounded bg-gray-100 text-gray-700">
                        {CATEGORIES.find(c => c.value === item.category)?.label || item.category}
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => handleDelete(item.id, item.issuer || 'Item')}
                    disabled={deletingId === item.id}
                    className="text-red-600 hover:text-red-800 disabled:opacity-50"
                    title="Excluir"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <div className="bg-gray-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <DollarSign className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">Nenhuma transação encontrada</h3>
          <p className="text-sm text-gray-600 mb-4">Comece adicionando sua primeira receita ou despesa</p>
          <Link
            to="/bills/add"
            className="inline-flex items-center px-4 py-2 bg-gray-900 text-white rounded-md hover:bg-gray-800 font-semibold text-sm transition-colors"
          >
            <Plus className="w-4 h-4 mr-2" />
            Adicionar Primeira Transação
          </Link>
        </div>
      )}
    </div>
  )
}

