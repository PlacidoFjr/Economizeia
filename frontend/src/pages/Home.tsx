import { Link } from 'react-router-dom'
import { motion } from 'motion/react'
import {
  ArrowRight,
  BarChart3,
  Bot,
  CalendarClock,
  CheckCircle,
  Shield,
  Target,
  TrendingUp,
  WalletCards,
} from 'lucide-react'
import ThemeToggle from '../components/ThemeToggle'

const FEATURES = [
  {
    icon: Bot,
    title: 'Chat financeiro econômico',
    description: 'Responde dúvidas do dia a dia e ajuda a registrar gastos, receitas e contas com rapidez.',
  },
  {
    icon: WalletCards,
    title: 'Lançamentos rápidos',
    description: 'Registre gastos, receitas, contas pagas e parcelas em poucos segundos.',
  },
  {
    icon: BarChart3,
    title: 'Dashboard do mês',
    description: 'Acompanhe receitas, despesas, saldo, categorias, emissores e evolução.',
  },
  {
    icon: CalendarClock,
    title: 'Histórico mensal',
    description: 'Volte para meses anteriores e confira gastos, pagamentos e parcelados.',
  },
  {
    icon: Target,
    title: 'Metas e investimentos',
    description: 'Organize objetivos financeiros e acompanhe sua carteira no mesmo lugar.',
  },
  {
    icon: Shield,
    title: 'Privacidade por padrão',
    description: 'Cada conta mantém suas informações separadas, com acesso protegido e controle individual.',
  },
]

const STEPS = [
  { icon: WalletCards, title: 'Registre', text: 'Despesas, receitas, contas pagas e parcelas.' },
  { icon: Bot, title: 'Pergunte', text: 'Consulte pendências, vencidos, saldo e categorias.' },
  { icon: TrendingUp, title: 'Ajuste', text: 'Use o painel para decidir o próximo movimento.' },
]

const BENEFITS = [
  'Controle total das suas finanças',
  'Menos gasto com IA paga',
  'Relatórios profissionais',
  'Segurança e privacidade garantidas',
]

export default function Home() {
  return (
    <div className="min-h-screen bg-white text-slate-950 dark:bg-slate-950 dark:text-white">
      <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/92 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/92">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link to="/" className="notranslate text-xl font-bold text-slate-950 sm:text-2xl dark:text-white" translate="no">
            Economize<span className="text-cyan-600 dark:text-cyan-400">IA</span>
          </Link>
          <div className="flex items-center gap-2 sm:gap-4">
            <ThemeToggle />
            <Link to="/login" className="px-2 text-sm font-semibold text-slate-600 transition-colors hover:text-slate-950 sm:text-base dark:text-slate-300 dark:hover:text-white">
              Entrar
            </Link>
            <Link
              to="/register"
              className="inline-flex items-center gap-2 rounded-lg bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-slate-300 transition-colors hover:bg-slate-800 sm:px-6 dark:bg-white dark:text-slate-950 dark:shadow-none dark:hover:bg-slate-200"
            >
              Começar agora
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </header>

      <section className="border-b border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto grid min-h-[calc(100vh-64px)] max-w-7xl items-center gap-10 px-4 py-14 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
            className="max-w-3xl"
          >
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan-200 bg-cyan-50 px-4 py-2 text-xs font-semibold text-cyan-800 dark:border-cyan-500/30 dark:bg-cyan-400/10 dark:text-cyan-200">
              <CheckCircle className="h-4 w-4" />
              Organização financeira com chat econômico
            </div>
            <h1 className="text-4xl font-bold leading-tight text-slate-950 sm:text-5xl lg:text-6xl dark:text-white">
              Controle suas finanças sem depender de crédito de IA para tudo.
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-8 text-slate-600 sm:text-lg dark:text-slate-300">
              O EconomizeIA reúne despesas, receitas, contas, metas, investimentos e um assistente para acompanhar sua rotina financeira com clareza.
            </p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Link
                to="/register"
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-slate-950 px-6 py-4 text-base font-semibold text-white shadow-lg transition-colors hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
              >
                Criar conta grátis
                <ArrowRight className="h-5 w-5" />
              </Link>
              <Link
                to="/login"
                className="inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-6 py-4 text-base font-semibold text-slate-800 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:hover:bg-slate-800"
              >
                Já tenho conta
              </Link>
            </div>
          </motion.div>

          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950">
            <div className="mb-5 flex items-center justify-between border-b border-slate-200 pb-4 dark:border-slate-800">
              <div>
                <p className="text-xs font-semibold uppercase text-cyan-700 dark:text-cyan-300">Resumo do mês</p>
                <p className="mt-1 text-2xl font-bold text-slate-950 dark:text-white">R$ 2.840</p>
              </div>
              <span className="rounded-md bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-400/10 dark:text-emerald-300">
                +18%
              </span>
            </div>
            <div className="space-y-3">
              {[
                ['Receitas', 'R$ 5.200', 'bg-emerald-500'],
                ['Despesas', 'R$ 2.360', 'bg-red-500'],
                ['Parcelados', 'R$ 480', 'bg-cyan-500'],
              ].map(([label, value, color]) => (
                <div key={label} className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span className="font-semibold text-slate-700 dark:text-slate-300">{label}</span>
                    <span className="font-bold text-slate-950 dark:text-white">{value}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                    <div className={`h-full rounded-full ${color}`} style={{ width: label === 'Receitas' ? '82%' : label === 'Despesas' ? '46%' : '24%' }} />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-5 grid grid-cols-2 gap-3">
              {BENEFITS.slice(0, 2).map((benefit) => (
                <div key={benefit} className="rounded-lg bg-slate-50 p-3 text-xs font-semibold text-slate-700 dark:bg-slate-900 dark:text-slate-300">
                  {benefit}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="bg-white py-16 sm:py-20 dark:bg-slate-950">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mb-10 max-w-3xl">
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-700 dark:text-cyan-300">Fluxo diário</p>
            <h2 className="text-3xl font-bold text-slate-950 sm:text-4xl dark:text-white">Menos abas, menos planilhas soltas, mais clareza.</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {STEPS.map((step) => {
              const Icon = step.icon
              return (
                <div key={step.title} className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                  <div className="mb-5 inline-flex rounded-md bg-slate-950 p-3 dark:bg-white">
                    <Icon className="h-5 w-5 text-cyan-300 dark:text-cyan-700" />
                  </div>
                  <h3 className="text-lg font-bold text-slate-950 dark:text-white">{step.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{step.text}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      <section className="bg-slate-50 py-16 sm:py-20 dark:bg-slate-900">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mb-10 text-center">
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700 dark:text-emerald-300">Recursos</p>
            <h2 className="text-3xl font-bold text-slate-950 sm:text-4xl dark:text-white">Tudo que sustenta sua rotina financeira</h2>
            <p className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300">
              A experiência foi pensada para consulta rápida, registro simples e visão financeira organizada.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature) => {
              const Icon = feature.icon
              return (
                <div key={feature.title} className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm transition-colors hover:border-slate-300 dark:border-slate-800 dark:bg-slate-950 dark:hover:border-slate-700">
                  <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-md bg-slate-100 dark:bg-slate-900">
                    <Icon className="h-5 w-5 text-slate-800 dark:text-slate-200" />
                  </div>
                  <h3 className="text-lg font-bold text-slate-950 dark:text-white">{feature.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{feature.description}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      <section className="bg-slate-950 py-16 text-white sm:py-20">
        <div className="mx-auto flex max-w-5xl flex-col items-center px-4 text-center sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold sm:text-4xl">Pronto para deixar o dinheiro mais previsível?</h2>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300">
            Comece pelo básico: registre o que entra e sai. O EconomizeIA organiza o resto para você consultar sem atrito.
          </p>
          <Link
            to="/register"
            className="mt-8 inline-flex items-center gap-2 rounded-lg bg-white px-7 py-4 text-base font-semibold text-slate-950 transition-colors hover:bg-cyan-50"
          >
            Criar conta grátis
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>
    </div>
  )
}
