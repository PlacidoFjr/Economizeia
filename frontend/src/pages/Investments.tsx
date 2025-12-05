import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import { Plus, TrendingUp, Edit, Trash2, X, ArrowUp, ArrowDown } from 'lucide-react'

interface Investment {
  id: string
  name: string
  type: string
  amount_invested: number
  current_value: number | null
  purchase_date: string
  sell_date: string | null
  institution: string | null
  ticker: string | null
  notes: string | null
  profit_loss: number
  profit_loss_percentage: number
}

const INVESTMENT_TYPES = [
  { value: 'stock', label: 'Ações' },
  { value: 'fixed_income', label: 'Renda Fixa' },
  { value: 'fund', label: 'Fundos' },
  { value: 'crypto', label: 'Criptomoedas' },
  { value: 'real_estate', label: 'Imóveis' },
  { value: 'other', label: 'Outros' },
]

export default function Investments() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [formData, setFormData] = useState({
    name: '',
    type: 'stock',
    amount_invested: '',
    current_value: '',
    purchase_date: '',
    sell_date: '',
    institution: '',
    ticker: '',
    notes: '',
  })

  const { data: investments, isLoading } = useQuery<Investment[]>({
    queryKey: ['investments', typeFilter],
    queryFn: async () => {
      const params = typeFilter ? `?type_filter=${typeFilter}` : ''
      const response = await api.get(`/investments${params}`)
      return response.data
    },
  })

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/investments', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investments'] })
      setShowForm(false)
      setFormData({
        name: '',
        type: 'stock',
        amount_invested: '',
        current_value: '',
        purchase_date: '',
        sell_date: '',
        institution: '',
        ticker: '',
        notes: '',
      })
    },
  })

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: any }) => {
      const response = await api.put(`/investments/${id}`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investments'] })
      setEditingId(null)
      setShowForm(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/investments/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investments'] })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const data: any = {
      name: formData.name,
      type: formData.type,
      amount_invested: parseFloat(formData.amount_invested),
      purchase_date: formData.purchase_date,
      institution: formData.institution || undefined,
      ticker: formData.ticker || undefined,
      notes: formData.notes || undefined,
    }
    if (formData.current_value) {
      data.current_value = parseFloat(formData.current_value)
    }
    if (formData.sell_date) {
      data.sell_date = formData.sell_date
    }

    if (editingId) {
      updateMutation.mutate({ id: editingId, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const handleDelete = (id: string, name: string) => {
    if (!confirm(`Deseja realmente excluir o investimento "${name}"?`)) return
    deleteMutation.mutate(id)
  }

  const startEdit = (investment: Investment) => {
    setEditingId(investment.id)
    setFormData({
      name: investment.name,
      type: investment.type,
      amount_invested: investment.amount_invested.toString(),
      current_value: investment.current_value?.toString() || '',
      purchase_date: investment.purchase_date,
      sell_date: investment.sell_date || '',
      institution: investment.institution || '',
      ticker: investment.ticker || '',
      notes: investment.notes || '',
    })
    setShowForm(true)
  }

  const getTypeLabel = (type: string) => {
    return INVESTMENT_TYPES.find((t) => t.value === type)?.label || type
  }

  const totalInvested = investments?.reduce((sum, inv) => sum + inv.amount_invested, 0) || 0
  const totalCurrent = investments?.reduce((sum, inv) => sum + (inv.current_value || inv.amount_invested), 0) || 0
  const totalProfitLoss = totalCurrent - totalInvested
  const totalProfitLossPercentage = totalInvested > 0 ? (totalProfitLoss / totalInvested) * 100 : 0

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-3"></div>
          <p className="text-sm text-gray-600">Carregando investimentos...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Investimentos</h1>
          <p className="mt-2 text-gray-600">Gerencie seus investimentos e acompanhe o desempenho</p>
        </div>
        <button
          onClick={() => {
            setShowForm(true)
            setEditingId(null)
            setFormData({
              name: '',
              type: 'stock',
              amount_invested: '',
              current_value: '',
              purchase_date: '',
              sell_date: '',
              institution: '',
              ticker: '',
              notes: '',
            })
          }}
          className="flex items-center gap-2 bg-gray-900 text-white px-4 py-2 rounded-lg font-semibold hover:bg-gray-800 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Novo Investimento
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-lg border-2 border-gray-200 p-6">
          <p className="text-sm text-gray-600 mb-1">Total Investido</p>
          <p className="text-2xl font-bold text-gray-900">
            R$ {totalInvested.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
          </p>
        </div>
        <div className="bg-white rounded-lg border-2 border-gray-200 p-6">
          <p className="text-sm text-gray-600 mb-1">Valor Atual</p>
          <p className="text-2xl font-bold text-gray-900">
            R$ {totalCurrent.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
          </p>
        </div>
        <div className="bg-white rounded-lg border-2 border-gray-200 p-6">
          <p className="text-sm text-gray-600 mb-1">Lucro/Prejuízo</p>
          <p
            className={`text-2xl font-bold ${
              totalProfitLoss >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {totalProfitLoss >= 0 ? '+' : ''}
            {totalProfitLoss.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
          </p>
        </div>
        <div className="bg-white rounded-lg border-2 border-gray-200 p-6">
          <p className="text-sm text-gray-600 mb-1">Rentabilidade</p>
          <p
            className={`text-2xl font-bold ${
              totalProfitLossPercentage >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {totalProfitLossPercentage >= 0 ? '+' : ''}
            {totalProfitLossPercentage.toFixed(2)}%
          </p>
        </div>
      </div>

      {/* Filter */}
      <div className="mb-6">
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
        >
          <option value="">Todos os tipos</option>
          {INVESTMENT_TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-gray-900">
                {editingId ? 'Editar Investimento' : 'Novo Investimento'}
              </h2>
              <button
                onClick={() => {
                  setShowForm(false)
                  setEditingId(null)
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nome do Investimento
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
                    placeholder="Ex: PETR4"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tipo
                  </label>
                  <select
                    required
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
                  >
                    {INVESTMENT_TYPES.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Valor Investido (R$)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={formData.amount_invested}
                    onChange={(e) => setFormData({ ...formData, amount_invested: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Valor Atual (R$)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.current_value}
                    onChange={(e) => setFormData({ ...formData, current_value: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
                    placeholder="Opcional"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Data de Compra
                  </label>
                  <input
                    type="date"
                    required
                    value={formData.purchase_date}
                    onChange={(e) => setFormData({ ...formData, purchase_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Data de Venda (opcional)
                  </label>
                  <input
                    type="date"
                    value={formData.sell_date}
                    onChange={(e) => setFormData({ ...formData, sell_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Instituição/Corretora
                  </label>
                  <input
                    type="text"
                    value={formData.institution}
                    onChange={(e) => setFormData({ ...formData, institution: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
                    placeholder="Ex: XP Investimentos"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ticker/Código
                  </label>
                  <input
                    type="text"
                    value={formData.ticker}
                    onChange={(e) => setFormData({ ...formData, ticker: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
                    placeholder="Ex: PETR4, BTC"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Observações
                </label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
                  rows={3}
                  placeholder="Observações sobre o investimento..."
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  className="flex-1 bg-gray-900 text-white px-4 py-2 rounded-lg font-semibold hover:bg-gray-800 transition-colors"
                >
                  {editingId ? 'Salvar' : 'Criar Investimento'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false)
                    setEditingId(null)
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Investments List */}
      {!investments || investments.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border-2 border-dashed border-gray-300">
          <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">Você ainda não tem investimentos cadastrados</p>
          <button
            onClick={() => setShowForm(true)}
            className="inline-flex items-center gap-2 bg-gray-900 text-white px-4 py-2 rounded-lg font-semibold hover:bg-gray-800 transition-colors"
          >
            <Plus className="w-5 h-5" />
            Adicionar Primeiro Investimento
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg border-2 border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Investimento
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tipo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Investido
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Valor Atual
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Lucro/Prejuízo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rentabilidade
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {investments.map((investment) => (
                <tr key={investment.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{investment.name}</div>
                      {investment.ticker && (
                        <div className="text-sm text-gray-500">{investment.ticker}</div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                      {getTypeLabel(investment.type)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    R$ {investment.amount_invested.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    R$ {(investment.current_value || investment.amount_invested).toLocaleString('pt-BR', {
                      minimumFractionDigits: 2,
                    })}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-1">
                      {investment.profit_loss >= 0 ? (
                        <ArrowUp className="w-4 h-4 text-green-600" />
                      ) : (
                        <ArrowDown className="w-4 h-4 text-red-600" />
                      )}
                      <span
                        className={`text-sm font-semibold ${
                          investment.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {investment.profit_loss >= 0 ? '+' : ''}
                        {investment.profit_loss.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`text-sm font-semibold ${
                        investment.profit_loss_percentage >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {investment.profit_loss_percentage >= 0 ? '+' : ''}
                      {investment.profit_loss_percentage.toFixed(2)}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => startEdit(investment)}
                        className="text-gray-600 hover:text-gray-900"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(investment.id, investment.name)}
                        className="text-red-600 hover:text-red-900"
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
      )}
    </div>
  )
}

