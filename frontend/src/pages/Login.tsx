import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../hooks/useToast'
import { Shield, TrendingUp, Zap, Mail, Lock, ArrowLeft } from 'lucide-react'
import { AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

// Dados de exemplo para os gráficos
const growthData = [
  { name: 'Mês 1', usuarios: 100 },
  { name: 'Mês 2', usuarios: 250 },
  { name: 'Mês 3', usuarios: 450 },
  { name: 'Mês 4', usuarios: 700 },
  { name: 'Mês 5', usuarios: 1000 },
  { name: 'Mês 6', usuarios: 1500 },
]

const featuresData = [
  { name: 'OCR', value: 40, color: '#06b6d4' }, // cyan-500 - mais visível
  { name: 'IA', value: 30, color: '#3b82f6' }, // blue-500
  { name: 'Automação', value: 20, color: '#8b5cf6' }, // violet-500
  { name: 'Relatórios', value: 10, color: '#10b981' }, // emerald-500
]

const BENEFITS = [
  { icon: Zap, title: 'Processamento Rápido', desc: 'OCR e IA processam seus boletos em segundos' },
  { icon: Shield, title: '100% Seguro', desc: 'Seus dados protegidos com criptografia avançada' },
  { icon: TrendingUp, title: 'Controle Total', desc: 'Acompanhe todas suas finanças em um só lugar' },
]

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      await login(email, password)
      showToast('Login realizado com sucesso!', 'success')
      navigate('/app/dashboard')
    } catch (err: any) {
      console.error('❌ Erro no login:', err)
      
      // Extrair mensagem de erro do backend
      let errorMessage = 'Erro ao fazer login. Tente novamente.'
      const backendMessage = err.response?.data?.detail || err.message || ''
      const statusCode = err.response?.status
      
      // Traduzir mensagens do backend para português amigável
      if (backendMessage.includes('não verificado') || backendMessage.includes('verificar') || backendMessage.includes('Email não verificado')) {
        errorMessage = 'Seu email ainda não foi verificado. Verifique sua caixa de entrada e clique no link de confirmação que enviamos.'
      } else if (backendMessage.includes('incorretos') || backendMessage.includes('senha') || backendMessage.includes('Email ou senha')) {
        errorMessage = 'Email ou senha incorretos. Verifique suas credenciais e tente novamente.'
      } else if (backendMessage.includes('inativa') || backendMessage.includes('inativo')) {
        errorMessage = 'Sua conta está inativa. Entre em contato com o suporte para mais informações.'
      } else if (backendMessage.includes('conectar') || backendMessage.includes('timeout') || backendMessage.includes('Network Error') || backendMessage.includes('API não configurada')) {
        errorMessage = 'Não foi possível conectar ao servidor. Verifique sua conexão com a internet e tente novamente.'
      } else if (statusCode === 401) {
        errorMessage = 'Email ou senha incorretos. Verifique suas credenciais.'
      } else if (statusCode === 403) {
        errorMessage = 'Acesso negado. Verifique se seu email foi confirmado ou entre em contato com o suporte.'
      } else if (statusCode === 404) {
        errorMessage = 'Usuário não encontrado. Verifique se o email está correto.'
      } else if (statusCode === 500) {
        errorMessage = 'Erro no servidor. Tente novamente em alguns instantes.'
      } else if (backendMessage && !backendMessage.includes('Erro')) {
        // Se o backend retornou uma mensagem amigável, usar ela
        errorMessage = backendMessage
      }
      
      showToast(errorMessage, 'error', 8000)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Lado Esquerdo - Gráficos e Benefícios */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-12 flex-col justify-between relative overflow-y-auto">
        {/* Decoração de fundo sutil */}
        <div className="absolute inset-0 opacity-5">
          <div className="absolute top-0 left-0 w-96 h-96 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-slate-400 rounded-full blur-3xl"></div>
        </div>

        <div className="relative z-10">
          <div className="mb-10">
            <h1 className="text-3xl font-bold text-white mb-2">
              <span className="text-white">Economize</span>
              <span className="text-cyan-400">IA</span>
            </h1>
            <p className="text-slate-300 text-base">A Sua Economia Inteligente</p>
          </div>

          {/* Gráfico de crescimento */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg p-6 mb-6 border border-slate-700/50">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-slate-100 font-semibold text-base flex items-center">
                <TrendingUp className="w-4 h-4 mr-2 text-cyan-400" />
                Crescimento de Usuários
              </h3>
              <span className="text-slate-300 text-xs font-medium">Últimos 6 meses</span>
            </div>
            <ResponsiveContainer width="100%" height={160}>
              <AreaChart data={growthData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorUsuarios" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.4}/>
                    <stop offset="100%" stopColor="#06b6d4" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis 
                  dataKey="name" 
                  stroke="#cbd5e1" 
                  fontSize={11}
                  fontWeight={500}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis 
                  stroke="#cbd5e1" 
                  fontSize={11}
                  fontWeight={500}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#0f172a', 
                    border: '1px solid #1e293b',
                    borderRadius: '8px',
                    padding: '10px 14px',
                    color: '#f1f5f9',
                    fontSize: '13px',
                    fontWeight: '500'
                  }}
                  labelStyle={{ color: '#cbd5e1', marginBottom: '4px', fontSize: '12px', fontWeight: '600' }}
                  formatter={(value: number) => [`${value.toLocaleString()}`, 'Usuários']}
                />
                <Area 
                  type="monotone" 
                  dataKey="usuarios" 
                  stroke="#06b6d4" 
                  strokeWidth={2.5}
                  fillOpacity={1} 
                  fill="url(#colorUsuarios)"
                  dot={{ fill: '#06b6d4', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 5, fill: '#06b6d4' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Gráfico de recursos */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg p-6 border border-slate-700/50" style={{ outline: 'none' }}>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-slate-100 font-semibold text-base flex items-center">
                <Zap className="w-4 h-4 mr-2 text-cyan-400" />
                Recursos Disponíveis
              </h3>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={featuresData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={false}
                  outerRadius={70}
                  innerRadius={35}
                  fill="#64748b"
                  dataKey="value"
                  stroke="#1e293b"
                  strokeWidth={2}
                  isAnimationActive={true}
                  animationBegin={0}
                  animationDuration={800}
                >
                  {featuresData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.color}
                      stroke="none"
                    />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e293b', 
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    padding: '12px 16px',
                    color: '#ffffff',
                    fontSize: '14px',
                    fontWeight: '600',
                    outline: 'none',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.5)'
                  }}
                  labelStyle={{
                    color: '#ffffff',
                    fontSize: '14px',
                    fontWeight: '600',
                    marginBottom: '4px'
                  }}
                  itemStyle={{
                    color: '#ffffff',
                    fontSize: '13px',
                    fontWeight: '500'
                  }}
                  cursor={false}
                  formatter={(value: number, name: string) => [`${name}: ${value}%`, '']}
                  separator=""
                />
              </PieChart>
            </ResponsiveContainer>
            {/* Legenda profissional */}
            <div className="grid grid-cols-2 gap-3 mt-6">
              {featuresData.map((entry, index) => (
                <div 
                  key={index} 
                  className="bg-slate-700/50 rounded-lg p-3 border border-slate-600/50 flex items-center space-x-3"
                >
                  <div 
                    className="w-4 h-4 rounded"
                    style={{ backgroundColor: entry.color }}
                  ></div>
                  <div className="flex-1 min-w-0">
                    <p className="text-slate-100 font-semibold text-sm truncate">{entry.name}</p>
                    <p className="text-slate-300 text-xs font-medium">{entry.value}%</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Benefícios */}
        <div className="relative z-10 space-y-2.5">
          {BENEFITS.map((benefit, index) => {
            const Icon = benefit.icon
            return (
              <div key={index} className="bg-slate-800/40 rounded-lg p-3.5 border border-slate-700/50 flex items-start">
                <div className="bg-slate-700/60 p-1.5 rounded mr-3 flex-shrink-0">
                  <Icon className="w-4 h-4 text-cyan-400" />
                </div>
                <div>
                  <p className="text-slate-100 font-semibold text-sm mb-1">{benefit.title}</p>
                  <p className="text-slate-300 text-xs leading-relaxed">{benefit.desc}</p>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Lado Direito - Formulário de Login */}
      <div className="w-full lg:w-1/2 flex items-center justify-center bg-white min-h-screen px-4 sm:px-6 lg:px-8 py-8 lg:py-16 lg:sticky lg:top-0 lg:h-screen lg:overflow-y-auto">
        <div className="max-w-md w-full space-y-6 lg:py-8">
          {/* Botão Voltar */}
          <div className="mb-4">
            <button
              onClick={() => navigate('/')}
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors group"
            >
              <ArrowLeft className="w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform" />
              <span className="text-sm font-medium">Voltar para Home</span>
            </button>
          </div>

          {/* Logo e título - mobile otimizado */}
          <div className="text-center lg:text-left mb-8 lg:mb-6">
            <h1 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-3">
              <span className="text-gray-900">Economize</span>
              <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">IA</span>
            </h1>
            <p className="text-sm lg:text-base text-gray-600">
              Acesse sua conta para continuar
            </p>
          </div>

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-5">
              <div>
                <label htmlFor="email" className="block text-sm font-semibold text-gray-700 mb-2">
                  Email
                </label>
                <div className="relative">
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    autoComplete="email"
                    className="appearance-none relative block w-full px-4 py-3.5 pl-12 border-2 border-gray-300 placeholder-gray-400 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 text-base transition-colors"
                    placeholder="seu@email.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Mail className="w-5 h-5 text-gray-400" />
                  </div>
                </div>
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-semibold text-gray-700 mb-2">
                  Senha
                </label>
                <div className="relative">
                  <input
                    id="password"
                    name="password"
                    type="password"
                    required
                    autoComplete="current-password"
                    className="appearance-none relative block w-full px-4 py-3.5 pl-12 border-2 border-gray-300 placeholder-gray-400 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 text-base transition-colors"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Lock className="w-5 h-5 text-gray-400" />
                  </div>
                </div>
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center items-center py-4 px-4 border border-transparent text-base font-semibold rounded-lg text-white bg-gray-900 hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Entrando...
                  </>
                ) : (
                  'Entrar'
                )}
              </button>
            </div>

            <div className="text-center space-y-3 pt-2">
              <Link
                to="/forgot-password"
                className="block text-sm text-gray-600 hover:text-gray-900 transition-colors font-medium"
              >
                Esqueci minha senha
              </Link>
              <div className="text-sm text-gray-600">
                Não tem conta?{' '}
                <Link
                  to="/register"
                  className="font-semibold text-gray-900 hover:text-gray-700 transition-colors underline"
                >
                  Criar conta
                </Link>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
