import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import { Plus, Target, Calendar, DollarSign, TrendingUp, Edit, Trash2, X, Check } from 'lucide-react'

interface SavingsGoal {
  id: string
  name: string
  target_amount: number
  current_amount: number
  deadline: string
  description?: string
  status: string
  progress_percentage: number
  days_remaining: number
  notify_days_before: number[]
}

export default function SavingsGoals() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [addingAmountId, setAddingAmountId] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    target_amount: '',
    deadline: '',
    description: '',
  })
  const [addAmount, setAddAmount] = useState('')

  const { data: goals, isLoading } = useQuery<SavingsGoal[]>({
    queryKey: ['savings-goals'],
    queryFn: async () => {
      const response = await api.get('/savings-goals')
      return response.data
    },
  })

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/savings-goals', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savings-goals'] })
      setShowForm(false)
      setFormData({ name: '', target_amount: '', deadline: '', description: '' })
    },
  })

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: any }) => {
      const response = await api.put(`/savings-goals/${id}`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savings-goals'] })
      setEditingId(null)
    },
  })

  const addAmountMutation = useMutation({
    mutationFn: async ({ id, amount }: { id: string; amount: number }) => {
      const response = await api.post(`/savings-goals/${id}/add-amount`, null, {
        params: { amount },
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savings-goals'] })
      setAddingAmountId(null)
      setAddAmount('')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/savings-goals/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savings-goals'] })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (editingId) {
      updateMutation.mutate({
        id: editingId,
        data: {
          name: formData.name,
          target_amount: parseFloat(formData.target_amount),
          deadline: formData.deadline,
          description: formData.description,
        },
      })
    } else {
      createMutation.mutate({
        name: formData.name,
        target_amount: parseFloat(formData.target_amount),
        deadline: formData.deadline,
        description: formData.description,
        notify_days_before: [30, 15, 7, 3, 1],
      })
    }
  }

  const handleAddAmount = (id: string) => {
    if (!addAmount || parseFloat(addAmount) <= 0) return
    addAmountMutation.mutate({ id, amount: parseFloat(addAmount) })
  }

  const handleDelete = (id: string, name: string) => {
    if (!confirm(`Deseja realmente excluir a meta "${name}"?`)) return
    deleteMutation.mutate(id)
  }

  const startEdit = (goal: SavingsGoal) => {
    setEditingId(goal.id)
    setFormData({
      name: goal.name,
      target_amount: goal.target_amount.toString(),
      deadline: goal.deadline,
      description: goal.description || '',
    })
    setShowForm(true)
  }

  const getStatusColor = (status: string, daysRemaining: number) => {
    if (status === 'completed') return 'bg-green-100 text-green-800'
    if (status === 'expired') return 'bg-red-100 text-red-800'
    if (daysRemaining <= 7) return 'bg-yellow-100 text-yellow-800'
    return 'bg-blue-100 text-blue-800'
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-3"></div>
          <p className="text-sm text-gray-600">Carregando metas...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Metas de Economia</h1>
          <p className="mt-2 text-gray-600">Defina e acompanhe suas metas de economia</p>
        </div>
        <button
          onClick={() => {
            setShowForm(true)
            setEditingId(null)
            setFormData({ name: '', target_amount: '', deadline: '', description: '' })
          }}
          className="flex items-center gap-2 bg-gray-900 text-white px-4 py-2 rounded-lg font-semibold hover:bg-gray-800 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Nova Meta
        </button>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-gray-900">
                {editingId ? 'Editar Meta' : 'Nova Meta de Economia'}
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
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome da Meta
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
                  placeholder="Ex: Viagem para Europa"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Valor a Guardar (R$)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  value={formData.target_amount}
                  onChange={(e) => setFormData({ ...formData, target_amount: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
                  placeholder="0.00"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Data Limite
                </label>
                <input
                  type="date"
                  required
                  value={formData.deadline}
                  onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descrição (opcional)
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
                  rows={3}
                  placeholder="Descreva sua meta..."
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  className="flex-1 bg-gray-900 text-white px-4 py-2 rounded-lg font-semibold hover:bg-gray-800 transition-colors"
                >
                  {editingId ? 'Salvar' : 'Criar Meta'}
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

      {/* Goals List */}
      {!goals || goals.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border-2 border-dashed border-gray-300">
          <Target className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">Você ainda não tem metas de economia</p>
          <button
            onClick={() => setShowForm(true)}
            className="inline-flex items-center gap-2 bg-gray-900 text-white px-4 py-2 rounded-lg font-semibold hover:bg-gray-800 transition-colors"
          >
            <Plus className="w-5 h-5" />
            Criar Primeira Meta
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {goals.map((goal) => (
            <div
              key={goal.id}
              className="bg-white rounded-lg border-2 border-gray-200 p-6 hover:border-gray-300 transition-colors"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-gray-900 mb-1">{goal.name}</h3>
                  {goal.description && (
                    <p className="text-sm text-gray-600 mb-2">{goal.description}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => startEdit(goal)}
                    className="p-1.5 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition-colors"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(goal.id, goal.name)}
                    className="p-1.5 text-red-600 hover:text-red-900 hover:bg-red-50 rounded transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-gray-600">Progresso</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {goal.progress_percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${
                      goal.progress_percentage >= 100
                        ? 'bg-green-500'
                        : goal.days_remaining <= 7
                        ? 'bg-yellow-500'
                        : 'bg-blue-500'
                    }`}
                    style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}
                  />
                </div>
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600 flex items-center gap-1">
                    <DollarSign className="w-4 h-4" />
                    Guardado
                  </span>
                  <span className="text-sm font-semibold text-gray-900">
                    R$ {goal.current_amount.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600 flex items-center gap-1">
                    <Target className="w-4 h-4" />
                    Meta
                  </span>
                  <span className="text-sm font-semibold text-gray-900">
                    R$ {goal.target_amount.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600 flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    Prazo
                  </span>
                  <span className="text-sm font-semibold text-gray-900">
                    {new Date(goal.deadline).toLocaleDateString('pt-BR')}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600 flex items-center gap-1">
                    <TrendingUp className="w-4 h-4" />
                    Restam
                  </span>
                  <span
                    className={`text-sm font-semibold ${
                      goal.days_remaining <= 7 ? 'text-red-600' : 'text-gray-900'
                    }`}
                  >
                    {goal.days_remaining} {goal.days_remaining === 1 ? 'dia' : 'dias'}
                  </span>
                </div>
              </div>

              <div className="mb-4">
                <span
                  className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(
                    goal.status,
                    goal.days_remaining
                  )}`}
                >
                  {goal.status === 'completed'
                    ? 'Concluída'
                    : goal.status === 'expired'
                    ? 'Expirada'
                    : goal.status === 'cancelled'
                    ? 'Cancelada'
                    : 'Ativa'}
                </span>
              </div>

              {goal.status === 'active' && (
                <div className="border-t border-gray-200 pt-4">
                  {addingAmountId === goal.id ? (
                    <div className="flex gap-2">
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        value={addAmount}
                        onChange={(e) => setAddAmount(e.target.value)}
                        placeholder="Valor"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
                      />
                      <button
                        onClick={() => handleAddAmount(goal.id)}
                        className="p-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        <Check className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => {
                          setAddingAmountId(null)
                          setAddAmount('')
                        }}
                        className="p-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setAddingAmountId(goal.id)}
                      className="w-full bg-gray-900 text-white px-4 py-2 rounded-lg font-semibold hover:bg-gray-800 transition-colors"
                    >
                      Adicionar Valor
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}


