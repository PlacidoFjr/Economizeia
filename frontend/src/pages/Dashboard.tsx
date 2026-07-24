import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { startOfMonth } from 'date-fns'
import api from '../services/api'
import { AlertCircle, DollarSign, FileText, ArrowUpCircle, ArrowDownCircle, TrendingUp } from 'lucide-react'
import { translateStatus, translateCategory } from '../utils/translations'
import {
  BarChart, Bar, AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import LoadingSpinner from '../components/LoadingSpinner'
import MonthSelector from '../components/MonthSelector'

// Cores para os grÃ¡ficos (categorias e emissores)
const COLORS = ['#0f172a', '#0891b2', '#16a34a', '#f59e0b', '#ef4444', '#7c3aed', '#db2777', '#2563eb', '#0d9488', '#ea580c']
const CATEGORY_COLORS: Record<string, string> = {
  alimentacao: '#10b981',
  moradia: '#14b8a6',
  servicos: '#0891b2',
  transporte: '#f59e0b',
  saude: '#e11d48',
  investimentos: '#7c3aed',
  compras: '#2563eb',
  lazer: '#db2777',
  educacao: '#475569',
  outras: '#64748b',
  Outras: '#64748b',
}

const formatCurrency = (value: number) =>
  value.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: value >= 1000 ? 0 : 2,
    maximumFractionDigits: value >= 1000 ? 0 : 2,
  })

const formatAxisCurrency = (value: number) => {
  if (value === 0) return 'R$ 0'
  if (Math.abs(value) >= 1000) return `R$ ${(value / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} mil`
  return `R$ ${value.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}`
}

const chartCardClass = 'rounded-lg border border-slate-200 bg-white/92 p-4 shadow-sm backdrop-blur sm:p-5'

function ChartEmpty({ title }: { title: string }) {
  return (
    <div className="flex h-[240px] flex-col items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50 text-center text-slate-500">
      <FileText className="mb-3 h-8 w-8 text-slate-300" />
      <p className="text-sm font-semibold text-slate-600">{title}</p>
      <p className="mt-1 text-xs text-slate-500">Adicione lanÃ§amentos para preencher este grÃ¡fico.</p>
    </div>
  )
}

export default function Dashboard() {
  const [selectedMonth, setSelectedMonth] = useState(startOfMonth(new Date()))

  // Buscar dados do usuÃ¡rio atual
  const { data: currentUser } = useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const response = await api.get('/auth/me')
      return response.data
    },
    staleTime: 0, // Sempre buscar dados atualizados (sem cache)
    gcTime: 0, // NÃ£o manter cache apÃ³s desmontar
  })

  // Buscar boletos e finanÃ§as separadamente
  const { data: bills, isLoading: isLoadingBills } = useQuery({
    queryKey: ['bills'],
    queryFn: async () => {
      const response = await api.get('/bills?is_bill=true')
      return response.data
    },
  })

  const { data: finances, isLoading: isLoadingFinances } = useQuery({
    queryKey: ['finances'],
    queryFn: async () => {
      const response = await api.get('/bills?is_bill=false')
      return response.data
    },
  })

  const { data: investments, isLoading: isLoadingInvestments } = useQuery({
    queryKey: ['investments'],
    queryFn: async () => {
      try {
        const response = await api.get('/investments')
        return response.data || []
      } catch (error) {
        console.error('Erro ao buscar investimentos:', error)
        return []
      }
    },
  })

  const isLoading = isLoadingBills || isLoadingFinances || isLoadingInvestments

  // Processamento de dados com useMemo para otimizaÃ§Ã£o
  const { currentMonthYear, allTransactions, transactionsThisMonth, expensesThisMonth, incomeThisMonth, balanceThisMonth } = useMemo(() => {
    const currentMonth = selectedMonth.getMonth()
    const currentYear = selectedMonth.getFullYear()

    // Formatar mÃªs e ano atual em portuguÃªs
    const monthNames = [
      'Janeiro', 'Fevereiro', 'MarÃ§o', 'Abril', 'Maio', 'Junho',
      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    const currentMonthYear = `${monthNames[currentMonth]} ${currentYear}`

    // Combinar boletos e finanÃ§as para cÃ¡lculos
    const allTransactions = [...(bills || []), ...(finances || [])]

    // Filtrar transaÃ§Ãµes do mÃªs atual
    const transactionsThisMonth = allTransactions?.filter((b: any) => {
      if (!b.due_date) return false
      const dueDate = new Date(b.due_date)
      return dueDate.getMonth() === currentMonth && dueDate.getFullYear() === currentYear
    }) || []

    // Calcular despesas do mÃªs (todas as transaÃ§Ãµes de despesa pagas/confirmadas)
    const expensesThisMonth = transactionsThisMonth
      .filter((b: any) => b.type === 'expense' && (b.status === 'paid' || b.status === 'confirmed'))
      .reduce((sum: number, b: any) => sum + (b.amount || 0), 0)

    // Calcular receitas (todas as transaÃ§Ãµes de receita pagas/confirmadas)
    const incomeThisMonth = transactionsThisMonth
      .filter((b: any) => b.type === 'income' && (b.status === 'paid' || b.status === 'confirmed'))
      .reduce((sum: number, b: any) => sum + (b.amount || 0), 0) || 0

    // Saldo do mÃªs
    const balanceThisMonth = incomeThisMonth - expensesThisMonth

    return {
      currentMonthYear,
      allTransactions,
      transactionsThisMonth,
      expensesThisMonth,
      incomeThisMonth,
      balanceThisMonth
    }
  }, [bills, finances, selectedMonth])

  // Agrupar por categoria (usando todas as transaÃ§Ãµes) - memoizado
  const categoryChartData = useMemo(() => {
    const categoryData = transactionsThisMonth.reduce((acc: any, bill: any) => {
      if (bill.type === 'expense' && (bill.status === 'paid' || bill.status === 'confirmed')) {
        const category = bill.category || 'Outras'
        if (!acc[category]) {
          acc[category] = { name: category, value: 0, count: 0 }
        }
        acc[category].value += bill.amount || 0
        acc[category].count += 1
      }
      return acc
    }, {})

    return Object.values(categoryData).map((cat: any, index: number) => ({
      name: translateCategory(cat.name),
      value: cat.value,
      count: cat.count,
      color: CATEGORY_COLORS[cat.name] || COLORS[index % COLORS.length]
    })).sort((a: any, b: any) => b.value - a.value)
  }, [transactionsThisMonth])

  const totalCategoryExpenses = useMemo(
    () => categoryChartData.reduce((sum: number, cat: any) => sum + cat.value, 0),
    [categoryChartData]
  )

  // Agrupar por emissor (top 10) - memoizado
  const issuerChartData = useMemo(() => {
    const issuerData = transactionsThisMonth.reduce((acc: any, bill: any) => {
      if (bill.type === 'expense' && (bill.status === 'paid' || bill.status === 'confirmed')) {
        const issuer = bill.issuer || 'Desconhecido'
        if (!acc[issuer]) {
          acc[issuer] = { name: issuer, value: 0, count: 0 }
        }
        acc[issuer].value += bill.amount || 0
        acc[issuer].count += 1
      }
      return acc
    }, {})

    return Object.values(issuerData)
      .map((iss: any, index: number) => ({
        name: iss.name.length > 15 ? iss.name.substring(0, 15) + '...' : iss.name,
        fullName: iss.name,
        value: iss.value,
        count: iss.count,
        color: COLORS[index % COLORS.length]
      }))
      .sort((a: any, b: any) => b.value - a.value)
      .slice(0, 10)
  }, [transactionsThisMonth])

  // Dados mensais (Ãºltimos 6 meses) - memoizado
  const monthlyData = useMemo(() => {
    const currentMonth = selectedMonth.getMonth()
    const currentYear = selectedMonth.getFullYear()
    const data = []

    for (let i = 5; i >= 0; i--) {
      const date = new Date(currentYear, currentMonth - i, 1)
      const monthTransactions = allTransactions?.filter((b: any) => {
        if (!b.due_date) return false
        const dueDate = new Date(b.due_date)
        return dueDate.getMonth() === date.getMonth() && dueDate.getFullYear() === date.getFullYear()
      }) || []

      const expenses = monthTransactions
        .filter((b: any) => b.type === 'expense' && (b.status === 'paid' || b.status === 'confirmed'))
        .reduce((sum: number, b: any) => sum + (b.amount || 0), 0)

      const income = monthTransactions
        .filter((b: any) => b.type === 'income' && (b.status === 'paid' || b.status === 'confirmed'))
        .reduce((sum: number, b: any) => sum + (b.amount || 0), 0)

      data.push({
        name: date.toLocaleDateString('pt-BR', { month: 'short' }),
        month: date.getMonth(),
        year: date.getFullYear(),
        despesas: expenses,
        receitas: income,
        saldo: income - expenses,
      })
    }
    return data
  }, [allTransactions, selectedMonth])

  // Processar dados de investimentos - memoizado
  const { totalInvested, totalCurrentValue, totalProfitLoss, totalProfitLossPercent, investmentTypeChartData } = useMemo(() => {
    const totalInvested = investments?.reduce((sum: number, inv: any) => sum + (inv.amount_invested || 0), 0) || 0
    const totalCurrentValue = investments?.reduce((sum: number, inv: any) => sum + ((inv.current_value || inv.amount_invested) || 0), 0) || 0
    const totalProfitLoss = totalCurrentValue - totalInvested
    const totalProfitLossPercent = totalInvested > 0 ? ((totalProfitLoss / totalInvested) * 100) : 0

    // Agrupar investimentos por tipo
    const typeLabels: { [key: string]: string } = {
      stock: 'AÃ§Ãµes',
      fixed_income: 'Renda Fixa',
      fund: 'Fundos',
      crypto: 'Criptomoedas',
      real_estate: 'ImÃ³veis',
      other: 'Outros'
    }

    const investmentTypeData = (investments || []).reduce((acc: any, inv: any) => {
      const type = inv.type || 'other'
      const typeLabel = typeLabels[type] || 'Outros'

      if (!acc[type]) {
        acc[type] = { name: typeLabel, value: 0, count: 0, invested: 0, current: 0 }
      }
      acc[type].value += inv.current_value || inv.amount_invested || 0
      acc[type].invested += inv.amount_invested || 0
      acc[type].current += inv.current_value || inv.amount_invested || 0
      acc[type].count += 1
      return acc
    }, {})

    const investmentTypeChartData = Object.values(investmentTypeData)
      .map((inv: any, index: number) => ({
        ...inv,
        color: COLORS[index % COLORS.length],
        profit: inv.current - inv.invested,
        profitPercent: inv.invested > 0 ? ((inv.current - inv.invested) / inv.invested * 100) : 0
      }))
      .sort((a: any, b: any) => b.value - a.value)

    return {
      totalInvested,
      totalCurrentValue,
      totalProfitLoss,
      totalProfitLossPercent,
      investmentTypeChartData
    }
  }, [investments])

  // Dados para grÃ¡fico de receitas vs despesas - memoizado
  const incomeVsExpenses = useMemo(() => [
    { name: 'Receitas', valor: incomeThisMonth, color: '#10b981' }, // Verde para receitas
    { name: 'Despesas', valor: expensesThisMonth, color: '#ef4444' }, // Vermelho para despesas
  ], [incomeThisMonth, expensesThisMonth])

  // Filtrar apenas contas marcadas como algo a pagar/avisar.
  const { pendingBills, overdueBills, totalPending } = useMemo(() => {
    const pendingBills = transactionsThisMonth?.filter((b: any) =>
      (b.status === 'pending' || b.status === 'scheduled') &&
      b.type === 'expense'
    ) || []

    const overdueBills = transactionsThisMonth?.filter((b: any) => {
      if (!b.due_date) return false
      const dueDate = new Date(b.due_date)
      // Despesa comum confirmada nao vira alerta; so aviso/pagamento pendente.
      return dueDate < new Date() &&
             (b.status === 'pending' || b.status === 'scheduled') &&
             b.type === 'expense'
    }) || []

    const totalPending = pendingBills.reduce((sum: number, b: any) => sum + (b.amount || 0), 0)

    return { pendingBills, overdueBills, totalPending }
  }, [transactionsThisMonth])

  const recentTransactions = useMemo(() => {
    return [...(allTransactions || [])]
      .sort((a: any, b: any) => new Date(b.due_date || b.created_at || 0).getTime() - new Date(a.due_date || a.created_at || 0).getTime())
      .slice(0, 5)
  }, [allTransactions])
  // const scheduledPayments = payments?.filter((p: any) => p.status === 'scheduled').length || 0

  if (isLoading) {
    return <LoadingSpinner message="Carregando dados do painel..." />
  }

  return (
    <div className="space-y-4 sm:space-y-6 pb-20 sm:pb-6">
      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="relative bg-slate-950 px-5 py-6 text-white sm:px-7 sm:py-8">
          <div className="absolute inset-0 opacity-30 [background-image:linear-gradient(120deg,transparent_0%,rgba(34,211,238,0.18)_45%,rgba(52,211,153,0.16)_100%)]" />
          <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-200">Painel financeiro</p>
              <h1 className="text-2xl font-bold text-white sm:text-3xl lg:text-4xl">
                {currentUser?.name ? `Bem-vindo, ${currentUser.name}.` : 'Painel de Controle'}
              </h1>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">
                VisÃ£o geral do mÃªs com receitas, despesas, pendÃªncias e evoluÃ§Ã£o das suas finanÃ§as.
              </p>
            </div>
            <div className="flex flex-col gap-3">
              <MonthSelector value={selectedMonth} onChange={setSelectedMonth} compact />
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="rounded-md border border-white/10 bg-white/8 px-3 py-2 backdrop-blur">
                  <p className="text-lg font-bold text-white">{transactionsThisMonth.length}</p>
                  <p className="text-[11px] text-slate-400">lanÃ§amentos</p>
                </div>
                <div className="rounded-md border border-white/10 bg-white/8 px-3 py-2 backdrop-blur">
                  <p className="text-lg font-bold text-white">{pendingBills.length}</p>
                  <p className="text-[11px] text-slate-400">pendentes</p>
                </div>
                <div className="rounded-md border border-white/10 bg-white/8 px-3 py-2 backdrop-blur">
                  <p className="text-lg font-bold text-white">{overdueBills.length}</p>
                  <p className="text-[11px] text-slate-400">vencidos</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Principais */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 sm:gap-3 lg:gap-4">
        <div className="bg-white border border-green-200 p-4 sm:p-5 rounded-lg shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-[10px] sm:text-xs font-medium text-gray-600 mb-0.5 sm:mb-1">Receitas do MÃªs</p>
              <p className="text-lg sm:text-xl font-bold text-green-700 truncate">R$ {incomeThisMonth.toFixed(2)}</p>
              <p className="text-[10px] sm:text-xs text-gray-500 mt-0.5 sm:mt-1">{currentMonthYear}</p>
            </div>
            <div className="bg-green-100 p-1.5 sm:p-2 rounded flex-shrink-0 ml-2">
              <ArrowUpCircle className="w-4 h-4 sm:w-5 sm:h-5 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white border border-red-200 p-4 sm:p-5 rounded-lg shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-[10px] sm:text-xs font-medium text-gray-600 mb-0.5 sm:mb-1">Despesas do MÃªs</p>
              <p className="text-lg sm:text-xl font-bold text-red-700 truncate">R$ {expensesThisMonth.toFixed(2)}</p>
              <p className="text-[10px] sm:text-xs text-gray-500 mt-0.5 sm:mt-1">{currentMonthYear}</p>
            </div>
            <div className="bg-red-100 p-1.5 sm:p-2 rounded flex-shrink-0 ml-2">
              <ArrowDownCircle className="w-4 h-4 sm:w-5 sm:h-5 text-red-600" />
            </div>
          </div>
        </div>

        <div className={`bg-white border ${balanceThisMonth >= 0 ? 'border-green-200' : 'border-red-200'} p-4 sm:p-5 rounded-lg shadow-sm hover:shadow-md transition-shadow`}>
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-[10px] sm:text-xs font-medium text-gray-600 mb-0.5 sm:mb-1">Saldo do MÃªs</p>
              <p className={`text-lg sm:text-xl font-bold truncate ${balanceThisMonth >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                R$ {balanceThisMonth.toFixed(2)}
              </p>
              <p className={`text-[10px] sm:text-xs mt-0.5 sm:mt-1 ${balanceThisMonth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {balanceThisMonth >= 0 ? 'Positivo' : 'Negativo'}
              </p>
            </div>
            <div className={`p-1.5 sm:p-2 rounded flex-shrink-0 ml-2 ${balanceThisMonth >= 0 ? 'bg-green-100' : 'bg-red-100'}`}>
              <DollarSign className={`w-4 h-4 sm:w-5 sm:h-5 ${balanceThisMonth >= 0 ? 'text-green-600' : 'text-red-600'}`} />
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 p-4 sm:p-5 rounded-lg shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-[10px] sm:text-xs font-medium text-gray-600 mb-0.5 sm:mb-1">Contas Pendentes</p>
              <p className="text-lg sm:text-xl font-bold text-gray-900">{pendingBills.length}</p>
              <p className="text-[10px] sm:text-xs text-gray-500 mt-0.5 sm:mt-1">R$ {totalPending.toFixed(2)}</p>
            </div>
            <div className="bg-gray-100 p-1.5 sm:p-2 rounded flex-shrink-0 ml-2">
              <FileText className="w-4 h-4 sm:w-5 sm:h-5 text-gray-600" />
            </div>
          </div>
        </div>
      </div>

      {/* GrÃ¡ficos Principais */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
        {/* Receitas vs Despesas */}
        <div className={chartCardClass}>
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold text-slate-950">Receitas vs Despesas</h3>
              <p className="mt-1 text-xs text-slate-500">{currentMonthYear}</p>
            </div>
            <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${balanceThisMonth >= 0 ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
              {formatCurrency(balanceThisMonth)}
            </span>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={incomeVsExpenses} margin={{ top: 18, right: 8, left: 2, bottom: 0 }}>
              <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="#e2e8f0" />
              <XAxis
                dataKey="name"
                axisLine={false}
                tickLine={false}
                stroke="#64748b"
                fontSize={12}
                tick={{ fill: '#64748b', fontWeight: 600 }}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                stroke="#64748b"
                fontSize={11}
                tick={{ fill: '#64748b' }}
                tickFormatter={formatAxisCurrency}
                width={54}
              />
              <Tooltip
                formatter={(value: number) => [formatCurrency(value), 'Valor']}
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  padding: '10px',
                  fontSize: '13px',
                  boxShadow: '0 14px 30px rgba(15,23,42,0.12)'
                }}
                cursor={{ fill: 'rgba(15,23,42,0.04)' }}
              />
              <Bar dataKey="valor" radius={[8, 8, 3, 3]} barSize={64} isAnimationActive={false}>
                {incomeVsExpenses.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* DistribuiÃ§Ã£o por Categoria */}
        <div className={chartCardClass}>
          <div className="mb-4">
            <h3 className="text-sm font-bold text-slate-950">Gastos por Categoria</h3>
            <p className="mt-1 text-xs text-slate-500">DistribuiÃ§Ã£o de {currentMonthYear}</p>
          </div>
          {categoryChartData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={categoryChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={false}
                    outerRadius={92}
                    innerRadius={58}
                    fill="#8884d8"
                    dataKey="value"
                    paddingAngle={categoryChartData.length > 1 ? 3 : 0}
                    cornerRadius={categoryChartData.length > 1 ? 7 : 0}
                    isAnimationActive={false}
                  >
                    {categoryChartData.map((entry: any, index: number) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.color}
                        stroke="#fff"
                        strokeWidth={categoryChartData.length > 1 ? 3 : 0}
                      />
                    ))}
                  </Pie>
                  <text x="50%" y="47%" textAnchor="middle" className="fill-slate-950 text-sm font-bold">
                    {formatCurrency(totalCategoryExpenses)}
                  </text>
                  <text x="50%" y="57%" textAnchor="middle" className="fill-slate-500 text-[11px]">
                    total
                  </text>
                  <Tooltip
                    formatter={(value: number, _name: string, props: any) => [
                      formatCurrency(value),
                      props.payload.name
                    ]}
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      padding: '10px',
                      boxShadow: '0 14px 30px rgba(15,23,42,0.12)'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
                {categoryChartData.slice(0, 4).map((cat: any, index: number) => (
                  <div key={index} className="flex items-center space-x-2 rounded-lg bg-slate-50 p-3">
                    <div className="w-4 h-4 rounded-full flex-shrink-0" style={{ backgroundColor: cat.color }}></div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-slate-950 truncate">{cat.name}</p>
                      <p className="text-xs text-slate-600">{formatCurrency(cat.value)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <ChartEmpty title="Nenhuma categoria ainda" />
          )}
        </div>
      </div>

      {/* GrÃ¡ficos de Investimentos */}
      {investments && investments.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
          {/* DistribuiÃ§Ã£o de Investimentos por Tipo */}
          <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4 shadow-sm">
            <div className="flex items-center justify-between mb-3 sm:mb-4">
              <h3 className="text-xs sm:text-sm font-semibold text-gray-900">
                Investimentos por Tipo
              </h3>
              <TrendingUp className="w-5 h-5 text-blue-600" />
            </div>
            {investmentTypeChartData.length > 0 ? (
              <>
                <ResponsiveContainer width="100%" height={200} className="sm:h-[240px] lg:h-[280px]">
                  <PieChart>
                    <Pie
                      data={investmentTypeChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={false}
                      outerRadius={90}
                      innerRadius={40}
                      fill="#8884d8"
                      dataKey="value"
                      paddingAngle={2}
                      isAnimationActive={false}
                    >
                      {investmentTypeChartData.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={entry.color} stroke="#fff" strokeWidth={2} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: number, _name: string, props: any) => [
                        `R$ ${value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
                        props.payload.name
                      ]}
                      contentStyle={{
                        backgroundColor: 'white',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        padding: '10px',
                        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="mt-4 space-y-2">
                  {investmentTypeChartData.slice(0, 5).map((inv: any, index: number) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <div className="flex items-center space-x-2 flex-1 min-w-0">
                        <div className="w-4 h-4 rounded-full flex-shrink-0" style={{ backgroundColor: inv.color }}></div>
                        <span className="text-xs font-semibold text-gray-900 truncate">{inv.name}</span>
                      </div>
                      <div className="text-right ml-2">
                        <p className="text-xs font-semibold text-gray-900">
                          R$ {inv.value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </p>
                        <p className={`text-xs ${inv.profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {inv.profit >= 0 ? '+' : ''}{inv.profitPercent.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-[300px] text-gray-500">
                <div className="bg-gray-100 w-16 h-16 rounded-full flex items-center justify-center mb-3">
                  <TrendingUp className="w-8 h-8 text-gray-400" />
                </div>
                <p className="text-sm">Nenhum investimento cadastrado</p>
              </div>
            )}
          </div>

          {/* Resumo de Investimentos */}
          <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4 shadow-sm">
            <h3 className="text-xs sm:text-sm font-semibold text-gray-900 mb-3 sm:mb-4">
              Resumo de Investimentos
            </h3>
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-xs font-medium text-blue-700 mb-1">Total Investido</p>
                <p className="text-2xl font-bold text-blue-900">
                  R$ {totalInvested.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
              </div>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <p className="text-xs font-medium text-gray-700 mb-1">Valor Atual</p>
                <p className="text-2xl font-bold text-gray-900">
                  R$ {totalCurrentValue.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
              </div>
              <div className={`border rounded-lg p-4 ${totalProfitLoss >= 0 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                <p className="text-xs font-medium mb-1" style={{ color: totalProfitLoss >= 0 ? '#065f46' : '#991b1b' }}>
                  {totalProfitLoss >= 0 ? 'Lucro' : 'PrejuÃ­zo'}
                </p>
                <div className="flex items-baseline space-x-2">
                  <p className={`text-2xl font-bold ${totalProfitLoss >= 0 ? 'text-green-900' : 'text-red-900'}`}>
                    {totalProfitLoss >= 0 ? '+' : ''}R$ {Math.abs(totalProfitLoss).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                  <p className={`text-sm font-semibold ${totalProfitLoss >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                    ({totalProfitLossPercent >= 0 ? '+' : ''}{totalProfitLossPercent.toFixed(2)}%)
                  </p>
                </div>
              </div>
              <div className="pt-3 border-t border-gray-200">
                <p className="text-xs text-gray-600 mb-2">Total de Investimentos:</p>
                <p className="text-lg font-bold text-gray-900">{investments.length}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* GrÃ¡ficos SecundÃ¡rios */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
        {/* EvoluÃ§Ã£o Mensal - Receitas e Despesas */}
        <div className={chartCardClass}>
          <div className="mb-4">
            <h3 className="text-sm font-bold text-slate-950">EvoluÃ§Ã£o Financeira</h3>
            <p className="mt-1 text-xs text-slate-500">Ãšltimos 6 meses</p>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={monthlyData} margin={{ top: 14, right: 8, left: 2, bottom: 0 }}>
              <defs>
                <linearGradient id="colorReceitas" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.05}/>
                </linearGradient>
                <linearGradient id="colorDespesas" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0.05}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="#e2e8f0" />
              <XAxis
                dataKey="name"
                axisLine={false}
                tickLine={false}
                stroke="#64748b"
                fontSize={11}
                tick={{ fill: '#64748b', fontWeight: 600 }}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                stroke="#64748b"
                fontSize={11}
                tick={{ fill: '#64748b' }}
                tickFormatter={formatAxisCurrency}
                width={54}
              />
              <Tooltip
                formatter={(value: number, name: string) => [
                  formatCurrency(value),
                  name === 'receitas' ? 'Receitas' : name === 'despesas' ? 'Despesas' : 'Saldo'
                ]}
                labelFormatter={(label: string) => label}
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  padding: '10px',
                  fontSize: '13px',
                  boxShadow: '0 14px 30px rgba(15,23,42,0.12)'
                }}
              />
              <Legend
                formatter={(value) => value === 'receitas' ? 'Receitas' : value === 'despesas' ? 'Despesas' : 'Saldo'}
                iconType="circle"
                wrapperStyle={{ paddingTop: '10px' }}
              />
              <Area
                type="monotone"
                dataKey="receitas"
                stroke="#10b981"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#colorReceitas)"
                name="receitas"
                isAnimationActive={false}
              />
              <Area
                type="monotone"
                dataKey="despesas"
                stroke="#ef4444"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#colorDespesas)"
                name="despesas"
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Top Emissores */}
        <div className={chartCardClass}>
          <div className="mb-4">
            <h3 className="text-sm font-bold text-slate-950">Top Emissores</h3>
            <p className="mt-1 text-xs text-slate-500">Maiores gastos de {currentMonthYear}</p>
          </div>
          {issuerChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={issuerChartData} layout="vertical" margin={{ top: 5, right: 18, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="4 4" horizontal={false} stroke="#e2e8f0" />
                <XAxis
                  type="number"
                  axisLine={false}
                  tickLine={false}
                  stroke="#64748b"
                  fontSize={11}
                  tick={{ fill: '#64748b' }}
                  tickFormatter={formatAxisCurrency}
                />
                <YAxis
                  dataKey="name"
                  type="category"
                  axisLine={false}
                  tickLine={false}
                  stroke="#64748b"
                  width={92}
                  fontSize={11}
                  tick={{ fill: '#64748b', fontWeight: 600 }}
                />
                <Tooltip
                  formatter={(value: number, name: string, props: any) => [
                    formatCurrency(value),
                    props.payload.fullName || name
                  ]}
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    padding: '10px',
                    fontSize: '13px',
                    boxShadow: '0 14px 30px rgba(15,23,42,0.12)'
                  }}
                  cursor={{ fill: 'rgba(15,23,42,0.04)' }}
                />
                <Bar dataKey="value" radius={[0, 8, 8, 0]} barSize={34} isAnimationActive={false}>
                  {issuerChartData.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <ChartEmpty title="Nenhum emissor ainda" />
          )}
        </div>
      </div>

      {/* Alerts */}
      {overdueBills.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center mb-3">
            <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
            <h3 className="text-sm font-semibold text-red-900">AtenÃ§Ã£o: contas vencidas</h3>
          </div>
          <ul className="space-y-2">
            {overdueBills.slice(0, 5).map((bill: any) => (
              <li key={bill.id} className="bg-white rounded border border-red-100 p-2 text-sm">
                <span className="font-medium text-gray-900">{bill.issuer || 'Desconhecido'}</span>
                {' - '}
                <span className="font-semibold text-gray-900">R$ {bill.amount?.toFixed(2)}</span>
                {' - '}
                <span className="text-gray-600">Vencido em {new Date(bill.due_date).toLocaleDateString('pt-BR')}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recent Transactions */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="bg-gray-50 border-b border-gray-200 p-4">
          <h2 className="text-sm font-semibold text-gray-900">
            LanÃ§amentos Recentes
          </h2>
        </div>
        <div className="p-4">
          {recentTransactions.length > 0 ? (
            <div className="space-y-2">
              {recentTransactions.map((bill: any) => (
                <div key={bill.id} className="flex justify-between items-center p-3 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded transition-colors">
                  <div className="flex-1">
                    <p className="font-semibold text-sm text-gray-900 mb-0.5">{bill.issuer || 'Desconhecido'}</p>
                    <p className="text-xs text-gray-600">
                      Vencimento: <span className="text-gray-900">{bill.due_date ? new Date(bill.due_date).toLocaleDateString('pt-BR') : 'N/A'}</span>
                    </p>
                  </div>
                  <div className="text-right ml-4">
                    <p className="font-semibold text-sm text-gray-900 mb-1">R$ {bill.amount?.toFixed(2)}</p>
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
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
          ) : (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-sm text-gray-500">Nenhum lanÃ§amento encontrado</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
