import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'
import { DollarSign, Calendar, Tag, FileText, Save, X, TrendingUp, TrendingDown } from 'lucide-react'
import { useToast } from '../hooks/useToast'
import Breadcrumbs from '../components/Breadcrumbs'
import Button from '../components/Button'

const CATEGORIES = [
  { value: 'alimentacao', label: 'Alimentação' },
  { value: 'moradia', label: 'Moradia' },
  { value: 'servicos', label: 'Serviços' },
  { value: 'transporte', label: 'Transporte' },
  { value: 'saude', label: 'Saúde' },
  { value: 'investimentos', label: 'Investimentos' },
  { value: 'outras', label: 'Outras' },
]

const STATUS_OPTIONS = [
  { value: 'pending', label: 'Pendente' },
  { value: 'confirmed', label: 'Confirmado' },
  { value: 'scheduled', label: 'Agendado' },
]

export default function AddExpense() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  
  const [formData, setFormData] = useState({
    type: 'expense', // 'expense' ou 'income'
    issuer: '',
    amount: '',
    due_date: '',
    category: '',
    barcode: '',
    notes: '',
    status: 'confirmed',
  })
  
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      try {
        const response = await api.post('/bills/create', data)
        return response.data
      } catch (error: any) {
        console.error('Erro ao criar despesa/receita:', error)
        throw error
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bills'] })
      queryClient.invalidateQueries({ queryKey: ['finances'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      showToast(
        `${formData.type === 'income' ? 'Receita' : 'Despesa'} criada com sucesso!`,
        'success'
      )
      // Navegar para a página apropriada baseado no tipo
      navigate('/app/finances')
    },
    onError: (error: any) => {
      console.error('❌ Erro na mutation:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Erro ao criar despesa/receita'
      setErrors({ submit: errorMessage })
      showToast(errorMessage, 'error', 8000)
    },
  })

  const validateField = (name: string, value: string): string => {
    switch (name) {
      case 'amount': {
        if (!value) return 'Valor é obrigatório'
        const numValue = parseFloat(value)
        if (isNaN(numValue) || numValue <= 0) return 'Valor deve ser maior que zero'
        if (numValue > 1000000000) return 'Valor muito alto'
        return ''
      }
      case 'due_date': {
        if (!value) return 'Data de vencimento é obrigatória'
        const date = new Date(value)
        if (isNaN(date.getTime())) return 'Data inválida'
        return ''
      }
      case 'issuer':
        if (value && value.length > 255) return 'Emissor muito longo (máximo 255 caracteres)'
        return ''
      default:
        return ''
    }
  }

  const handleBlur = (name: string) => {
    setTouched({ ...touched, [name]: true })
    const error = validateField(name, formData[name as keyof typeof formData])
    if (error) {
      setErrors({ ...errors, [name]: error })
    } else {
      const newErrors = { ...errors }
      delete newErrors[name]
      setErrors(newErrors)
    }
  }

  const handleChange = (name: string, value: string) => {
    setFormData({ ...formData, [name]: value })
    // Validar em tempo real se o campo já foi tocado
    if (touched[name]) {
      const error = validateField(name, value)
      if (error) {
        setErrors({ ...errors, [name]: error })
      } else {
        const newErrors = { ...errors }
        delete newErrors[name]
        setErrors(newErrors)
      }
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Marcar todos os campos como tocados
    const allTouched: Record<string, boolean> = {}
    Object.keys(formData).forEach(key => {
      allTouched[key] = true
    })
    setTouched(allTouched)

    // Validações
    const newErrors: Record<string, string> = {}
    
    Object.keys(formData).forEach(key => {
      if (key === 'amount' || key === 'due_date') {
        const error = validateField(key, formData[key as keyof typeof formData])
        if (error) newErrors[key] = error
      }
    })

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      showToast('Por favor, corrija os erros no formulário', 'error')
      return
    }

    // Preparar dados
    const submitData = {
      type: formData.type,
      issuer: formData.issuer || undefined,
      amount: parseFloat(formData.amount),
      due_date: formData.due_date,
      category: formData.category || undefined,
      barcode: formData.barcode || undefined,
      notes: formData.notes || undefined,
      status: formData.status,
      is_bill: false, // Transações manuais não são boletos
    }

    createMutation.mutate(submitData)
  }

  // Data padrão: hoje + 30 dias
  const defaultDate = new Date()
  defaultDate.setDate(defaultDate.getDate() + 30)
  const defaultDateStr = defaultDate.toISOString().split('T')[0]

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Breadcrumbs 
        items={[
          { label: 'Finanças', to: '/app/finances' },
          { label: formData.type === 'income' ? 'Adicionar Receita' : 'Adicionar Despesa' }
        ]} 
      />
      <div className="rounded-lg bg-slate-950 p-5 text-white shadow-xl shadow-slate-300/40 sm:p-7">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-200">
          Registro manual
        </p>
        <h1 className="mb-2 text-2xl font-bold sm:text-3xl">
          {formData.type === 'income' ? 'Adicionar Receita' : 'Adicionar Despesa'}
        </h1>
        <p className="max-w-xl text-sm leading-6 text-slate-300">
          {formData.type === 'income' 
            ? 'Registre uma nova receita do mês' 
            : 'Crie uma nova despesa manualmente com categoria, data e observações'}
        </p>
      </div>

      {/* Toggle Despesa/Receita */}
      <div className="rounded-lg border border-slate-200 bg-white p-2 shadow-sm">
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => setFormData({ ...formData, type: 'expense' })}
            className={`flex min-h-[48px] items-center justify-center rounded-lg px-4 py-3 text-sm font-semibold transition-all sm:text-base ${
              formData.type === 'expense'
                ? 'bg-red-50 text-red-700 ring-1 ring-red-200'
                : 'bg-slate-50 text-gray-600 hover:bg-slate-100'
            }`}
          >
            <TrendingDown className="w-4 h-4 sm:w-5 sm:h-5 mr-1.5 sm:mr-2" />
            Despesa
          </button>
          <button
            type="button"
            onClick={() => setFormData({ ...formData, type: 'income' })}
            className={`flex min-h-[48px] items-center justify-center rounded-lg px-4 py-3 text-sm font-semibold transition-all sm:text-base ${
              formData.type === 'income'
                ? 'bg-green-50 text-green-700 ring-1 ring-green-200'
                : 'bg-slate-50 text-gray-600 hover:bg-slate-100'
            }`}
          >
            <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 mr-1.5 sm:mr-2" />
            Receita
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm sm:space-y-6 sm:p-6">
        {errors.submit && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-md p-3">
            <p className="text-sm font-medium">{errors.submit}</p>
          </div>
        )}

        {/* Emissor / Fonte */}
        <div>
          <label htmlFor="issuer" className="block text-sm font-semibold text-gray-700 mb-2">
            <FileText className="w-4 h-4 inline mr-1" />
            {formData.type === 'income' ? 'Fonte da Receita' : 'Emissor / Fornecedor'}
          </label>
          <input
            type="text"
            id="issuer"
            value={formData.issuer}
            onChange={(e) => handleChange('issuer', e.target.value)}
            onBlur={() => handleBlur('issuer')}
            className={`w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 ${
              errors.issuer ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder={formData.type === 'income' 
              ? 'Ex: Salário, Freelance, Vendas, etc.' 
              : 'Ex: Energia Elétrica, Supermercado, etc.'}
            maxLength={255}
          />
          {errors.issuer && (
            <p className="mt-1 text-sm text-red-600">{errors.issuer}</p>
          )}
        </div>

        {/* Valor */}
        <div>
          <label htmlFor="amount" className="block text-sm font-semibold text-gray-700 mb-2">
            <DollarSign className="w-4 h-4 inline mr-1" />
            Valor <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            id="amount"
            step="0.01"
            min="0.01"
            value={formData.amount}
            onChange={(e) => handleChange('amount', e.target.value)}
            onBlur={() => handleBlur('amount')}
            className={`w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 ${
              errors.amount ? 'border-red-300 bg-red-50' : 'border-gray-300'
            }`}
            placeholder="0.00"
            required
            aria-invalid={!!errors.amount}
            aria-describedby={errors.amount ? 'amount-error' : undefined}
          />
          {errors.amount && (
            <p id="amount-error" className="mt-1 text-sm text-red-600" role="alert">{errors.amount}</p>
          )}
        </div>

        {/* Data de Vencimento / Recebimento */}
        <div>
          <label htmlFor="due_date" className="block text-sm font-semibold text-gray-700 mb-2">
            <Calendar className="w-4 h-4 inline mr-1" />
            {formData.type === 'income' ? 'Data de Recebimento' : 'Data de Vencimento'} <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            id="due_date"
            value={formData.due_date || defaultDateStr}
            onChange={(e) => handleChange('due_date', e.target.value)}
            onBlur={() => handleBlur('due_date')}
            className={`w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 ${
              errors.due_date ? 'border-red-300 bg-red-50' : 'border-gray-300'
            }`}
            required
            aria-invalid={!!errors.due_date}
            aria-describedby={errors.due_date ? 'due_date-error' : undefined}
          />
          {errors.due_date && (
            <p id="due_date-error" className="mt-1 text-sm text-red-600" role="alert">{errors.due_date}</p>
          )}
        </div>

        {/* Categoria */}
        <div>
          <label htmlFor="category" className="block text-sm font-semibold text-gray-700 mb-2">
            <Tag className="w-4 h-4 inline mr-1" />
            Categoria
          </label>
          <select
            id="category"
            value={formData.category}
            onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
          >
            <option value="">Selecione uma categoria</option>
            {CATEGORIES.map((cat) => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>
        </div>

        {/* Status */}
        <div>
          <label htmlFor="status" className="block text-sm font-semibold text-gray-700 mb-2">
            Status
          </label>
          <select
            id="status"
            value={formData.status}
            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
          >
            {STATUS_OPTIONS.map((status) => (
              <option key={status.value} value={status.value}>
                {status.label}
              </option>
            ))}
          </select>
        </div>

        {/* Código de Barras */}
        <div>
          <label htmlFor="barcode" className="block text-sm font-semibold text-gray-700 mb-2">
            Código de Barras (opcional)
          </label>
          <input
            type="text"
            id="barcode"
            value={formData.barcode}
            onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
            placeholder="Digite o código de barras"
          />
        </div>

        {/* Observações */}
        <div>
          <label htmlFor="notes" className="block text-sm font-semibold text-gray-700 mb-2">
            {formData.type === 'income' ? 'Observações sobre a Receita' : 'Observações'}
          </label>
          <textarea
            id="notes"
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            rows={3}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
            placeholder={formData.type === 'income' 
              ? 'Adicione observações sobre esta receita...' 
              : 'Adicione observações sobre esta despesa...'}
          />
        </div>

        {/* Botões */}
        <div className="flex flex-col sm:flex-row justify-end space-y-2 sm:space-y-0 sm:space-x-3 pt-4 border-t border-gray-200">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/app/finances')}
            icon={X}
            className="w-full sm:w-auto"
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={createMutation.isPending}
            icon={Save}
            className="w-full sm:w-auto"
          >
            {formData.type === 'income' ? 'Salvar Receita' : 'Salvar Despesa'}
          </Button>
        </div>
      </form>
    </div>
  )
}

