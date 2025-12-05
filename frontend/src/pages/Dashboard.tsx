import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import { AlertCircle, DollarSign, FileText, ArrowUpCircle, ArrowDownCircle, TrendingUp } from 'lucide-react'
import { translateStatus, translateCategory } from '../utils/translations'
import { 
  BarChart, Bar, AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import LoadingSpinner from '../components/LoadingSpinner'

// Cores para os gráficos (categorias e emissores)
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1']

export default function Dashboard() {
  // Buscar dados do usuário atual
  const { data: currentUser } = useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const response = await api.get('/auth/me')
      return response.data
    },
    staleTime: 0, // Sempre buscar dados atualizados (sem cache)
    gcTime: 0, // Não manter cache após desmontar
  })

  // Buscar boletos e finanças separadamente
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

  // Processamento de dados com useMemo para otimização
  const { currentMonthYear, allTransactions, transactionsThisMonth, expensesThisMonth, incomeThisMonth, balanceThisMonth } = useMemo(() => {
    const now = new Date()
    const currentMonth = now.getMonth()
    const currentYear = now.getFullYear()
    
    // Formatar mês e ano atual em português
    const monthNames = [
      'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    const currentMonthYear = `${monthNames[currentMonth]} ${currentYear}`

    // Combinar boletos e finanças para cálculos
    const allTransactions = [...(bills || []), ...(finances || [])]

    // Filtrar transações do mês atual
    const transactionsThisMonth = allTransactions?.filter((b: any) => {
      if (!b.due_date) return false
      const dueDate = new Date(b.due_date)
      return dueDate.getMonth() === currentMonth && dueDate.getFullYear() === currentYear
    }) || []

    // Calcular despesas do mês (todas as transações de despesa pagas/confirmadas)
    const expensesThisMonth = transactionsThisMonth
      .filter((b: any) => b.type === 'expense' && (b.status === 'paid' || b.status === 'confirmed'))
      .reduce((sum: number, b: any) => sum + (b.amount || 0), 0)

    // Calcular receitas (todas as transações de receita pagas/confirmadas)
    const incomeThisMonth = transactionsThisMonth
      .filter((b: any) => b.type === 'income' && (b.status === 'paid' || b.status === 'confirmed'))
      .reduce((sum: number, b: any) => sum + (b.amount || 0), 0) || 0

    // Saldo do mês
    const balanceThisMonth = incomeThisMonth - expensesThisMonth

    return {
      currentMonthYear,
      allTransactions,
      transactionsThisMonth,
      expensesThisMonth,
      incomeThisMonth,
      balanceThisMonth
    }
  }, [bills, finances])

  // Agrupar por categoria (usando todas as transações) - memoizado
  const categoryChartData = useMemo(() => {
    const categoryData = transactionsThisMonth.reduce((acc: any, bill: any) => {
      if (bill.type === 'expense') { // Apenas despesas
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
      color: COLORS[index % COLORS.length]
    })).sort((a: any, b: any) => b.value - a.value)
  }, [transactionsThisMonth])

  // Agrupar por emissor (top 10) - memoizado
  const issuerChartData = useMemo(() => {
    const issuerData = transactionsThisMonth.reduce((acc: any, bill: any) => {
      if (bill.type === 'expense') { // Apenas despesas
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

  // Dados mensais (últimos 6 meses) - memoizado
  const monthlyData = useMemo(() => {
    const now = new Date()
    const currentMonth = now.getMonth()
    const currentYear = now.getFullYear()
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
  }, [allTransactions])

  // Processar dados de investimentos - memoizado
  const { totalInvested, totalCurrentValue, totalProfitLoss, totalProfitLossPercent, investmentTypeChartData } = useMemo(() => {
    const totalInvested = investments?.reduce((sum: number, inv: any) => sum + (inv.amount_invested || 0), 0) || 0
    const totalCurrentValue = investments?.reduce((sum: number, inv: any) => sum + ((inv.current_value || inv.amount_invested) || 0), 0) || 0
    const totalProfitLoss = totalCurrentValue - totalInvested
    const totalProfitLossPercent = totalInvested > 0 ? ((totalProfitLoss / totalInvested) * 100) : 0

    // Agrupar investimentos por tipo
    const typeLabels: { [key: string]: string } = {
      stock: 'Ações',
      fixed_income: 'Renda Fixa',
      fund: 'Fundos',
      crypto: 'Criptomoedas',
      real_estate: 'Imóveis',
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

  // Dados para gráfico de receitas vs despesas - memoizado
  const incomeVsExpenses = useMemo(() => [
    { name: 'Receitas', valor: incomeThisMonth, color: '#10b981' }, // Verde para receitas
    { name: 'Despesas', valor: expensesThisMonth, color: '#ef4444' }, // Vermelho para despesas
  ], [incomeThisMonth, expensesThisMonth])

  // Filtrar boletos pendentes e vencidos - memoizado
  const { pendingBills, overdueBills, totalPending } = useMemo(() => {
    const pendingBills = allTransactions?.filter((b: any) => 
      (b.status === 'pending' || b.status === 'confirmed') && 
      b.type === 'expense' && 
      b.is_bill === true
    ) || []
    
    const overdueBills = allTransactions?.filter((b: any) => {
      if (!b.due_date) return false
      const dueDate = new Date(b.due_date)
      // Apenas despesas/boletos vencidos (não receitas)
      return dueDate < new Date() && 
             b.status !== 'paid' && 
             b.type === 'expense' && 
             b.is_bill === true
    }) || []
    
    const totalPending = pendingBills.reduce((sum: number, b: any) => sum + (b.amount || 0), 0)
    
    return { pendingBills, overdueBills, totalPending }
  }, [allTransactions])
  // const scheduledPayments = payments?.filter((p: any) => p.status === 'scheduled').length || 0

  if (isLoading) {
    return <LoadingSpinner message="Carregando dados do painel..." />
  }

  return (
    <div className="space-y-4 sm:space-y-6 p-4 sm:p-6 pb-20 sm:pb-6">
      <div className="mb-4 sm:mb-6">
        <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-900 mb-1">Painel de Controle</h1>
        {currentUser?.name && (
          <p className="text-base sm:text-lg lg:text-xl font-semibold text-gray-700 mb-1">
            Bem-vindo, {currentUser.name}! 👋
          </p>
        )}
        <p className="text-xs sm:text-sm text-gray-600">Visão geral das suas finanças</p>
      </div>

      {/* Stats Principais */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 sm:gap-3 lg:gap-4">
        <div className="bg-white border border-green-200 p-3 sm:p-4 rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-[10px] sm:text-xs font-medium text-gray-600 mb-0.5 sm:mb-1">Receitas do Mês</p>
              <p className="text-lg sm:text-xl font-bold text-green-700 truncate">R$ {incomeThisMonth.toFixed(2)}</p>
              <p className="text-[10px] sm:text-xs text-gray-500 mt-0.5 sm:mt-1">{currentMonthYear}</p>
            </div>
            <div className="bg-green-100 p-1.5 sm:p-2 rounded flex-shrink-0 ml-2">
              <ArrowUpCircle className="w-4 h-4 sm:w-5 sm:h-5 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white border border-red-200 p-3 sm:p-4 rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-[10px] sm:text-xs font-medium text-gray-600 mb-0.5 sm:mb-1">Despesas do Mês</p>
              <p className="text-lg sm:text-xl font-bold text-red-700 truncate">R$ {expensesThisMonth.toFixed(2)}</p>
              <p className="text-[10px] sm:text-xs text-gray-500 mt-0.5 sm:mt-1">{currentMonthYear}</p>
            </div>
            <div className="bg-red-100 p-1.5 sm:p-2 rounded flex-shrink-0 ml-2">
              <ArrowDownCircle className="w-4 h-4 sm:w-5 sm:h-5 text-red-600" />
            </div>
          </div>
        </div>

        <div className={`bg-white border ${balanceThisMonth >= 0 ? 'border-green-200' : 'border-red-200'} p-3 sm:p-4 rounded-lg shadow-sm`}>
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-[10px] sm:text-xs font-medium text-gray-600 mb-0.5 sm:mb-1">Saldo do Mês</p>
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

        <div className="bg-white border border-gray-200 p-3 sm:p-4 rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-[10px] sm:text-xs font-medium text-gray-600 mb-0.5 sm:mb-1">Boletos Pendentes</p>
              <p className="text-lg sm:text-xl font-bold text-gray-900">{pendingBills.length}</p>
              <p className="text-[10px] sm:text-xs text-gray-500 mt-0.5 sm:mt-1">R$ {totalPending.toFixed(2)}</p>
            </div>
            <div className="bg-gray-100 p-1.5 sm:p-2 rounded flex-shrink-0 ml-2">
              <FileText className="w-4 h-4 sm:w-5 sm:h-5 text-gray-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Gráficos Principais */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
        {/* Receitas vs Despesas */}
        <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4 shadow-sm">
          <h3 className="text-xs sm:text-sm font-semibold text-gray-900 mb-3 sm:mb-4">
            Receitas vs Despesas (Mês Atual)
          </h3>
          <ResponsiveContainer width="100%" height={200} className="sm:h-[240px] lg:h-[280px]">
            <BarChart data={incomeVsExpenses} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
              <XAxis 
                dataKey="name" 
                stroke="#6b7280" 
                fontSize={12}
                tick={{ fill: '#6b7280' }}
              />
              <YAxis 
                stroke="#6b7280" 
                fontSize={11}
                tick={{ fill: '#6b7280' }}
                tickFormatter={(value) => `R$ ${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip 
                formatter={(value: number) => [`R$ ${value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, 'Valor']}
                contentStyle={{ 
                  backgroundColor: 'white', 
                  border: '1px solid #e5e7eb', 
                  borderRadius: '8px',
                  padding: '10px',
                  fontSize: '13px',
                  boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                }} 
                cursor={{ fill: 'rgba(0,0,0,0.05)' }}
              />
              <Bar dataKey="valor" radius={[8, 8, 0, 0]} barSize={60}>
                {incomeVsExpenses.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Distribuição por Categoria */}
        <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">
            Gastos por Categoria
          </h3>
          {categoryChartData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={200} className="sm:h-[240px] lg:h-[280px]">
                <PieChart>
                  <Pie
                    data={categoryChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(props: any) => {
                      if (!props || !props.name) return '';
                      const percent = props.percent || 0;
                      if (percent < 0.05) return ''; // Não mostrar labels muito pequenos
                      return `${(percent * 100).toFixed(0)}%`;
                    }}
                    outerRadius={90}
                    innerRadius={40}
                    fill="#8884d8"
                    dataKey="value"
                    paddingAngle={2}
                  >
                    {categoryChartData.map((entry: any, index: number) => (
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
              <div className="mt-4 grid grid-cols-2 gap-3">
                {categoryChartData.slice(0, 4).map((cat: any, index: number) => (
                  <div key={index} className="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                    <div className="w-4 h-4 rounded-full flex-shrink-0" style={{ backgroundColor: cat.color }}></div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-gray-900 truncate">{cat.name}</p>
                      <p className="text-xs text-gray-600">R$ {cat.value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-[300px] text-gray-500">
              <div className="bg-gray-100 w-16 h-16 rounded-full flex items-center justify-center mb-3">
                <FileText className="w-8 h-8 text-gray-400" />
              </div>
              <p className="text-sm">Nenhum dado de categoria disponível</p>
            </div>
          )}
        </div>
      </div>

      {/* Gráficos de Investimentos */}
      {investments && investments.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
          {/* Distribuição de Investimentos por Tipo */}
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
                      label={(props: any) => {
                        if (!props || !props.name) return '';
                        const percent = props.percent || 0;
                        if (percent < 0.05) return '';
                        return `${(percent * 100).toFixed(0)}%`;
                      }}
                      outerRadius={90}
                      innerRadius={40}
                      fill="#8884d8"
                      dataKey="value"
                      paddingAngle={2}
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
                  {totalProfitLoss >= 0 ? 'Lucro' : 'Prejuízo'}
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

      {/* Gráficos Secundários */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
        {/* Evolução Mensal - Receitas e Despesas */}
        <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4 shadow-sm">
          <h3 className="text-xs sm:text-sm font-semibold text-gray-900 mb-3 sm:mb-4">
            Evolução Financeira (Últimos 6 Meses)
          </h3>
          <ResponsiveContainer width="100%" height={200} className="sm:h-[240px] lg:h-[280px]">
            <AreaChart data={monthlyData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
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
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
              <XAxis 
                dataKey="name" 
                stroke="#6b7280" 
                fontSize={11}
                tick={{ fill: '#6b7280' }}
              />
              <YAxis 
                stroke="#6b7280" 
                fontSize={11}
                tick={{ fill: '#6b7280' }}
                tickFormatter={(value) => `R$ ${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip 
                formatter={(value: number, name: string) => [
                  `R$ ${value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
                  name === 'receitas' ? 'Receitas' : name === 'despesas' ? 'Despesas' : 'Saldo'
                ]}
                labelFormatter={(label: string) => label}
                contentStyle={{ 
                  backgroundColor: 'white', 
                  border: '1px solid #e5e7eb', 
                  borderRadius: '8px',
                  padding: '10px',
                  fontSize: '13px',
                  boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
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
              />
              <Area 
                type="monotone" 
                dataKey="despesas" 
                stroke="#ef4444" 
                strokeWidth={2.5}
                fillOpacity={1} 
                fill="url(#colorDespesas)"
                name="despesas"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Top Emissores */}
        <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4 shadow-sm">
          <h3 className="text-xs sm:text-sm font-semibold text-gray-900 mb-3 sm:mb-4">
            Top Emissores (Gastos)
          </h3>
          {issuerChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200} className="sm:h-[240px] lg:h-[280px]">
              <BarChart data={issuerChartData} layout="vertical" margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
                <XAxis 
                  type="number" 
                  stroke="#6b7280" 
                  fontSize={11}
                  tick={{ fill: '#6b7280' }}
                  tickFormatter={(value) => `R$ ${(value / 1000).toFixed(0)}k`}
                />
                <YAxis 
                  dataKey="name" 
                  type="category" 
                  stroke="#6b7280" 
                  width={100}
                  fontSize={11}
                  tick={{ fill: '#6b7280' }}
                />
                <Tooltip 
                  formatter={(value: number, name: string, props: any) => [
                    `R$ ${value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
                    props.payload.fullName || name
                  ]}
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '8px',
                    padding: '10px',
                    fontSize: '13px',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                  }} 
                  cursor={{ fill: 'rgba(0,0,0,0.05)' }}
                />
                <Bar dataKey="value" radius={[0, 8, 8, 0]} barSize={35}>
                  {issuerChartData.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex flex-col items-center justify-center h-[300px] text-gray-500">
              <div className="bg-gray-100 w-16 h-16 rounded-full flex items-center justify-center mb-3">
                <FileText className="w-8 h-8 text-gray-400" />
              </div>
              <p className="text-sm">Nenhum dado de emissor disponível</p>
            </div>
          )}
        </div>
      </div>

      {/* Alerts */}
      {overdueBills.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center mb-3">
            <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
            <h3 className="text-sm font-semibold text-red-900">Atenção: Boletos Vencidos</h3>
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

      {/* Recent Bills */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="bg-gray-50 border-b border-gray-200 p-4">
          <h2 className="text-sm font-semibold text-gray-900">
            Boletos Recentes
          </h2>
        </div>
        <div className="p-4">
          {bills && bills.length > 0 ? (
            <div className="space-y-2">
              {bills.slice(0, 5).map((bill: any) => (
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
              <p className="text-sm text-gray-500">Nenhum boleto encontrado</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
