import { Link } from 'react-router-dom'
import { 
  TrendingUp, 
  Shield, 
  Zap, 
  FileText, 
  BarChart3, 
  Calendar,
  CheckCircle,
  ArrowRight,
  Sparkles
} from 'lucide-react'

const FEATURES = [
  {
    icon: FileText,
    title: 'OCR Inteligente',
    description: 'Digitalize seus boletos e receitas. Nossa IA extrai automaticamente todas as informações importantes.',
  },
  {
    icon: Sparkles,
    title: 'IA Semântica',
    description: 'Classificação automática e inteligente de suas despesas e receitas por categoria.',
  },
  {
    icon: Calendar,
    title: 'Agendamento Inteligente',
    description: 'Programe pagamentos e recebimentos. Receba alertas antes dos vencimentos.',
  },
  {
    icon: BarChart3,
    title: 'Relatórios Detalhados',
    description: 'Visualize sua saúde financeira com gráficos e análises completas do seu orçamento.',
  },
  {
    icon: Shield,
    title: '100% Seguro',
    description: 'Seus dados protegidos com criptografia de ponta e conformidade com LGPD.',
  },
  {
    icon: Zap,
    title: 'Automação Total',
    description: 'Reconciliação automática com extratos bancários e notificações inteligentes.',
  },
]

const BENEFITS = [
  'Controle total das suas finanças',
  'Economia de tempo com automação',
  'Relatórios profissionais',
  'Segurança e privacidade garantidas',
]

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50 backdrop-blur-sm bg-white/95">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-14 sm:h-16">
            <div className="flex items-center">
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
                <span className="text-gray-900">Economize</span>
                <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">IA</span>
              </h1>
            </div>
            <div className="flex items-center space-x-2 sm:space-x-4">
              <Link
                to="/login"
                className="text-gray-600 hover:text-gray-900 font-medium transition-colors text-sm sm:text-base px-2 sm:px-0"
              >
                Entrar
              </Link>
              <Link
                to="/register"
                className="bg-gray-900 text-white px-4 sm:px-6 py-2 sm:py-2.5 rounded-lg font-semibold hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-all shadow-md hover:shadow-lg text-sm sm:text-base flex items-center gap-1 sm:gap-2"
              >
                <span className="hidden sm:inline">Começar Agora</span>
                <span className="sm:hidden">Começar</span>
                <ArrowRight className="w-3 h-3 sm:w-4 sm:h-4" />
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 lg:py-20 xl:py-32">
        <div className="text-center">
          <div className="inline-flex items-center gap-2 bg-gray-100 text-gray-700 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs sm:text-sm font-medium mb-6 sm:mb-8">
            <Sparkles className="w-3 h-3 sm:w-4 sm:h-4" />
            <span className="whitespace-nowrap">Organização Financeira Inteligente</span>
          </div>
          
          <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-4 sm:mb-6 leading-tight px-2">
            Transforme sua vida financeira com
            <br className="hidden sm:block" />
            <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
              Inteligência Artificial
            </span>
          </h1>
          
          <p className="text-sm sm:text-base lg:text-lg text-gray-600 mb-8 sm:mb-12 max-w-3xl mx-auto leading-relaxed px-2">
            Gerencie suas finanças pessoais de forma inteligente. Digitalize boletos, 
            categorize automaticamente e tenha controle total do seu orçamento.
          </p>

          {/* Benefits List */}
          <div className="flex flex-wrap justify-center gap-3 sm:gap-4 md:gap-6 text-gray-600 px-4">
            {BENEFITS.map((benefit, index) => (
              <div key={index} className="flex items-center gap-1.5 sm:gap-2">
                <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 text-gray-400 flex-shrink-0" />
                <span className="font-medium text-xs sm:text-sm md:text-base">{benefit}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-gray-50 py-12 sm:py-16 lg:py-20 xl:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10 sm:mb-12 lg:mb-16">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-3 sm:mb-4 px-2">
              Recursos Poderosos
            </h2>
            <p className="text-sm sm:text-base lg:text-lg text-gray-600 max-w-2xl mx-auto px-4">
              Tudo que você precisa para ter controle total das suas finanças
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
            {FEATURES.map((feature, index) => {
              const Icon = feature.icon
              return (
                <div
                  key={index}
                  className="bg-white rounded-lg p-6 sm:p-8 border-2 border-gray-200 hover:border-gray-300 hover:shadow-lg transition-all duration-200"
                >
                  <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-gray-100 flex items-center justify-center mb-4 sm:mb-6">
                    <Icon className="w-5 h-5 sm:w-6 sm:h-6 text-gray-700" />
                  </div>
                  <h3 className="text-base sm:text-lg font-bold text-gray-900 mb-2 sm:mb-3">
                    {feature.title}
                  </h3>
                  <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-12 sm:py-16 lg:py-20 xl:py-32 bg-gradient-to-b from-white to-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl sm:rounded-3xl p-8 sm:p-10 lg:p-12 xl:p-16 text-white shadow-2xl relative overflow-hidden">
            {/* Decoração de fundo */}
            <div className="absolute inset-0 opacity-10">
              <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500 rounded-full blur-3xl"></div>
              <div className="absolute bottom-0 left-0 w-64 h-64 bg-blue-500 rounded-full blur-3xl"></div>
            </div>
            
            <div className="relative z-10">
              <div className="inline-flex items-center justify-center w-16 h-16 sm:w-20 sm:h-20 mb-6 sm:mb-8 bg-white/10 rounded-full backdrop-blur-sm">
                <TrendingUp className="w-8 h-8 sm:w-10 sm:h-10 text-cyan-400" />
              </div>
              
              <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-4 sm:mb-6 leading-tight px-2">
                Pronto para transformar suas finanças?
              </h2>
              
              <p className="text-sm sm:text-base lg:text-lg text-gray-300 mb-6 sm:mb-8 max-w-2xl mx-auto leading-relaxed px-2">
                Comece agora e tenha controle total do seu dinheiro com inteligência artificial
              </p>
              
              <Link
                to="/register"
                className="inline-flex items-center gap-2 bg-white text-gray-900 px-6 sm:px-8 py-3 sm:py-4 rounded-xl font-semibold text-sm sm:text-base hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white transition-all duration-200 shadow-lg hover:shadow-xl hover:scale-105 transform"
              >
                Criar Conta Grátis
                <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-8 sm:py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4 sm:gap-0">
            <div className="mb-4 md:mb-0 text-center md:text-left">
              <h3 className="text-lg sm:text-xl font-bold text-white mb-1 sm:mb-2">
                <span className="text-white">Economize</span>
                <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">IA</span>
              </h3>
              <p className="text-xs sm:text-sm text-gray-400">Organização financeira inteligente</p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-6 text-xs sm:text-sm items-center">
              <Link to="/termos" className="text-gray-400 hover:text-white transition-colors font-medium">
                Termos de Uso
              </Link>
              <Link to="/privacidade" className="text-gray-400 hover:text-white transition-colors font-medium">
                Política de Privacidade
              </Link>
            </div>
          </div>
          <div className="mt-6 sm:mt-8 pt-6 sm:pt-8 border-t border-gray-800 text-center text-xs sm:text-sm text-gray-500">
            <p>© 2024 EconomizeIA. Todos os direitos reservados.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
