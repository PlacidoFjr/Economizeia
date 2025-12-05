import { useQuery } from '@tanstack/react-query'
import api from '../services/api'
import { AlertCircle, DollarSign, FileText, ArrowUpCircle, ArrowDownCircle } from 'lucide-react'
import { translateStatus } from '../utils/translations'
import { 
  BarChart, Bar, AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts'

// Cores para os gráficos (categorias e emissores)
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1']

export default function Dashboard() {
  // Buscar boletos e finanças separadamente
  const { data: bills } = useQuery({
    queryKey: ['bills'],
    queryFn: async () => {
      const response = await api.get('/bills?is_bill=true')
      return response.data
    },
  })

  const { data: finances } = useQuery({
    queryKey: ['finances'],
    queryFn: async () => {
      const response = await api.get('/bills?is_bill=false')
      return response.data
    },
  })

  // const { data: payments } = useQuery({
  //   queryKey: ['payments'],
  //   queryFn: async () => {
  //     const response = await api.get('/payments')
  //     return response.data
  //   },
  // })

  // Processamento de dados
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

  // Agrupar por categoria (usando todas as transações)
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

  const categoryChartData = Object.values(categoryData).map((cat: any, index: number) => ({
    name: cat.name,
    value: cat.value,
    count: cat.count,
    color: COLORS[index % COLORS.length]
  })).sort((a: any, b: any) => b.value - a.value)

  // Agrupar por emissor (top 10) - usando todas as transações
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

  const issuerChartData = Object.values(issuerData)
    .map((iss: any, index: number) => ({
      name: iss.name.length > 15 ? iss.name.substring(0, 15) + '...' : iss.name,
      fullName: iss.name,
      value: iss.value,
      count: iss.count,
      color: COLORS[index % COLORS.length]
    }))
    .sort((a: any, b: any) => b.value - a.value)
    .slice(0, 10)

  // Dados mensais (últimos 6 meses) - usando todas as transações
  const monthlyData = []
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

    monthlyData.push({
      name: date.toLocaleDateString('pt-BR', { month: 'short' }),
      month: date.getMonth(),
      year: date.getFullYear(),
      despesas: expenses,
      receitas: income,
    })
  }

  // Dados para gráfico de receitas vs despesas
  const incomeVsExpenses = [
    { name: 'Receitas', valor: incomeThisMonth, color: '#10b981' }, // Verde para receitas
    { name: 'Despesas', valor: expensesThisMonth, color: '#ef4444' }, // Vermelho para despesas
  ]

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
  // const scheduledPayments = payments?.filter((p: any) => p.status === 'scheduled').length || 0

  return (
    <div className="space-y-6 p-6">
      <div className="mb-6">
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 mb-1">Painel de Controle</h1>
        <p className="text-sm text-gray-600">Visão geral das suas finanças</p>
      </div>

      {/* Stats Principais */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <div className="bg-white border border-green-200 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600 mb-1">Receitas do Mês</p>
              <p className="text-xl font-bold text-green-700">R$ {incomeThisMonth.toFixed(2)}</p>
              <p className="text-xs text-gray-500 mt-1">{currentMonthYear}</p>
            </div>
            <div className="bg-green-100 p-2 rounded">
              <ArrowUpCircle className="w-5 h-5 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white border border-red-200 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600 mb-1">Despesas do Mês</p>
              <p className="text-xl font-bold text-red-700">R$ {expensesThisMonth.toFixed(2)}</p>
              <p className="text-xs text-gray-500 mt-1">{currentMonthYear}</p>
            </div>
            <div className="bg-red-100 p-2 rounded">
              <ArrowDownCircle className="w-5 h-5 text-red-600" />
            </div>
          </div>
        </div>

        <div className={`bg-white border ${balanceThisMonth >= 0 ? 'border-green-200' : 'border-red-200'} p-4 rounded-lg`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600 mb-1">Saldo do Mês</p>
              <p className={`text-xl font-bold ${balanceThisMonth >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                R$ {balanceThisMonth.toFixed(2)}
              </p>
              <p className={`text-xs mt-1 ${balanceThisMonth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {balanceThisMonth >= 0 ? 'Positivo' : 'Negativo'}
              </p>
            </div>
            <div className={`p-2 rounded ${balanceThisMonth >= 0 ? 'bg-green-100' : 'bg-red-100'}`}>
              <DollarSign className={`w-5 h-5 ${balanceThisMonth >= 0 ? 'text-green-600' : 'text-red-600'}`} />
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600 mb-1">Boletos Pendentes</p>
              <p className="text-xl font-bold text-gray-900">{pendingBills.length}</p>
              <p className="text-xs text-gray-500 mt-1">R$ {totalPending.toFixed(2)}</p>
            </div>
            <div className="bg-gray-100 p-2 rounded">
              <FileText className="w-5 h-5 text-gray-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Gráficos Principais */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Receitas vs Despesas */}
        <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4">
          <h3 className="text-xs sm:text-sm font-semibold text-gray-900 mb-3 sm:mb-4">
            Receitas vs Despesas (Mês Atual)
          </h3>
          <ResponsiveContainer width="100%" height={200} className="sm:h-[250px]">
            <BarChart data={incomeVsExpenses}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" stroke="#6b7280" fontSize={11} />
              <YAxis stroke="#6b7280" fontSize={11} />
              <Tooltip 
                formatter={(value: number) => `R$ ${value.toFixed(2)}`}
                contentStyle={{ 
                  backgroundColor: 'white', 
                  border: '1px solid #e5e7eb', 
                  borderRadius: '6px',
                  padding: '8px',
                  fontSize: '12px'
                }} 
              />
              <Bar dataKey="valor" radius={[4, 4, 0, 0]}>
                {incomeVsExpenses.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Distribuição por Categoria */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">
            Gastos por Categoria
          </h3>
          {categoryChartData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={200} className="sm:h-[250px]">
                <PieChart>
                  <Pie
                    data={categoryChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(props: any) => {
                      if (!props || !props.name) return '';
                      const percent = props.percent || 0;
                      return `${props.name} ${(percent * 100).toFixed(0)}%`;
                    }}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {categoryChartData.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value: number) => `R$ ${value.toFixed(2)}`}
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #e5e7eb', 
                      borderRadius: '8px',
                      padding: '10px'
                    }} 
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="mt-4 grid grid-cols-2 gap-2">
                {categoryChartData.slice(0, 4).map((cat: any, index: number) => (
                  <div key={index} className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: cat.color }}></div>
                    <span className="text-sm text-gray-700 font-medium">{cat.name}</span>
                    <span className="text-sm text-gray-600">R$ {cat.value.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-500">
              <p>Nenhum dado de categoria disponível</p>
            </div>
          )}
        </div>
      </div>

      {/* Gráficos Secundários */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
        {/* Evolução Mensal */}
        <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4">
          <h3 className="text-xs sm:text-sm font-semibold text-gray-900 mb-3 sm:mb-4">
            Evolução de Despesas (Últimos 6 Meses)
          </h3>
          <ResponsiveContainer width="100%" height={200} className="sm:h-[250px]">
            <AreaChart data={monthlyData}>
              <defs>
                <linearGradient id="colorDespesas" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0.05}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" stroke="#6b7280" fontSize={11} />
              <YAxis stroke="#6b7280" fontSize={11} />
              <Tooltip 
                formatter={(value: number) => `R$ ${value.toFixed(2)}`}
                contentStyle={{ 
                  backgroundColor: 'white', 
                  border: '1px solid #e5e7eb', 
                  borderRadius: '6px',
                  padding: '8px',
                  fontSize: '12px'
                }} 
              />
              <Area 
                type="monotone" 
                dataKey="despesas" 
                stroke="#ef4444" 
                strokeWidth={2}
                fillOpacity={1} 
                fill="url(#colorDespesas)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Top Emissores */}
        <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4">
          <h3 className="text-xs sm:text-sm font-semibold text-gray-900 mb-3 sm:mb-4">
            Top Emissores (Gastos)
          </h3>
          {issuerChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200} className="sm:h-[300px]">
              <BarChart data={issuerChartData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis type="number" stroke="#6b7280" />
                <YAxis dataKey="name" type="category" stroke="#6b7280" width={100} />
                <Tooltip 
                  formatter={(value: number, name: string, props: any) => [
                    `R$ ${value.toFixed(2)}`,
                    props.payload.fullName || name
                  ]}
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '1px solid #e5e7eb', 
                    borderRadius: '8px',
                    padding: '10px'
                  }} 
                />
                <Bar dataKey="value" radius={[0, 8, 8, 0]}>
                  {issuerChartData.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-500">
              <p>Nenhum dado de emissor disponível</p>
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
