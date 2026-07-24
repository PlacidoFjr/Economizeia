import { lazy, Suspense, useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { motion } from 'motion/react'
import { Calendar, CreditCard, DollarSign, Home, LogOut, Menu, Target, TrendingUp, Upload, X } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import ThemeToggle from './ThemeToggle'

const Chatbot = lazy(() => import('./Chatbot'))

export default function Layout() {
  const { logout } = useAuth()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const handleLogout = async () => {
    queryClient.clear()
    await logout()
    navigate('/login')
  }

  const menuItems = [
    { to: '/app/dashboard', icon: Home, label: 'Painel' },
    { to: '/app/finances', icon: DollarSign, label: 'Finanças' },
    { to: '/app/transactions/add', icon: Upload, label: 'Adicionar' },
    { to: '/app/payments', icon: Calendar, label: 'Pagamentos' },
    { to: '/app/installments', icon: CreditCard, label: 'Parcelados' },
    { to: '/app/savings-goals', icon: Target, label: 'Metas' },
    { to: '/app/investments', icon: TrendingUp, label: 'Investimentos' },
  ]

  const bottomItems = menuItems.filter((item) =>
    ['/app/dashboard', '/app/finances', '/app/transactions/add', '/app/payments', '/app/installments'].includes(item.to)
  )

  useEffect(() => {
    setMobileMenuOpen(false)
  }, [location.pathname])

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-slate-100 dark:bg-slate-950">
      <Suspense fallback={null}>
        <Chatbot />
      </Suspense>

      <nav className="sticky top-0 z-50 border-b border-slate-200 bg-white/92 shadow-sm backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/92">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 justify-between">
            <div className="flex items-center">
              <Link to="/app/dashboard" className="flex items-center px-2 text-lg font-bold text-slate-950 transition-colors hover:text-slate-700 sm:px-4 sm:text-xl dark:text-white dark:hover:text-slate-200">
                Economize<span className="text-cyan-600 dark:text-cyan-400">IA</span>
              </Link>

              <div className="ml-5 hidden min-[900px]:flex min-[900px]:space-x-0.5 xl:ml-8 xl:space-x-1">
                {menuItems.map((item) => {
                  const Icon = item.icon
                  return (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      className={({ isActive }) =>
                        `flex items-center rounded-md px-2 py-2 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-500 xl:px-3 xl:text-sm ${
                          isActive
                            ? 'bg-slate-900 text-white shadow-sm dark:bg-white dark:text-slate-950'
                            : 'text-slate-700 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-900 dark:hover:text-white'
                        }`
                      }
                      aria-label={item.label}
                    >
                      <Icon className="mr-1.5 h-4 w-4 xl:mr-2" aria-hidden="true" />
                      {item.label}
                    </NavLink>
                  )
                })}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <ThemeToggle />
              <button
                onClick={() => void handleLogout()}
                className="hidden items-center rounded-md px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 hover:text-slate-950 min-[900px]:flex dark:text-slate-300 dark:hover:bg-slate-900 dark:hover:text-white"
              >
                <LogOut className="mr-2 h-4 w-4" />
                Sair
              </button>

              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="flex min-h-[44px] min-w-[44px] items-center justify-center rounded-md p-2 text-slate-700 transition-colors hover:bg-slate-100 hover:text-slate-950 min-[900px]:hidden dark:text-slate-300 dark:hover:bg-slate-900 dark:hover:text-white"
                aria-label="Menu"
              >
                {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
            </div>
          </div>
        </div>

        {mobileMenuOpen && (
          <div className="border-t border-slate-200 bg-white shadow-lg min-[900px]:hidden md:absolute md:right-4 md:top-16 md:w-80 md:rounded-b-lg md:border md:border-t-0 dark:border-slate-800 dark:bg-slate-950">
            <div className="grid grid-cols-1 gap-1 px-2 pb-3 pt-2">
              {menuItems.map((item) => {
                const Icon = item.icon
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={() => setMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      `flex min-h-[44px] items-center rounded-md px-3 py-2 text-base font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-slate-500 ${
                        isActive
                          ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-950'
                          : 'text-slate-700 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-900 dark:hover:text-white'
                      }`
                    }
                    aria-label={item.label}
                  >
                    <Icon className="mr-3 h-5 w-5" aria-hidden="true" />
                    {item.label}
                  </NavLink>
                )
              })}
              <button
                onClick={() => {
                  void handleLogout()
                  setMobileMenuOpen(false)
                }}
                className="flex w-full items-center rounded-md px-3 py-2 text-base font-medium text-slate-700 transition-colors hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-900 dark:hover:text-white"
              >
                <LogOut className="mr-3 h-5 w-5" />
                Sair
              </button>
            </div>
          </div>
        )}
      </nav>

      <motion.main
        key={location.pathname}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.18, ease: 'easeOut' }}
        className="relative z-10 mx-auto max-w-7xl px-4 py-5 pb-28 sm:px-6 sm:py-8 md:pb-8 lg:px-8"
      >
        <Outlet />
      </motion.main>

      <div className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/94 px-2 py-2 shadow-[0_-12px_30px_rgba(15,23,42,0.08)] backdrop-blur-xl md:hidden dark:border-slate-800 dark:bg-slate-950/94">
        <div className="mx-auto grid max-w-lg grid-cols-5 gap-1">
          {bottomItems.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex min-h-[54px] flex-col items-center justify-center rounded-lg px-1 text-[11px] font-semibold transition-colors ${
                    isActive
                      ? 'bg-slate-900 text-white shadow-md dark:bg-white dark:text-slate-950'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-900 dark:hover:text-white'
                  }`
                }
                aria-label={item.label}
              >
                <Icon className="mb-1 h-5 w-5" aria-hidden="true" />
                <span className="max-w-full truncate">{item.label}</span>
              </NavLink>
            )
          })}
        </div>
      </div>
    </div>
  )
}
