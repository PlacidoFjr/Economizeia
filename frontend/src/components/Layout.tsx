import { useState } from 'react'
import { Outlet, Link, useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext'
import { Home, FileText, Upload, LogOut, Calendar, CreditCard, Menu, X, DollarSign, Target, TrendingUp } from 'lucide-react'
import Chatbot from './Chatbot'

export default function Layout() {
  const { logout } = useAuth()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const handleLogout = () => {
    // Limpar todos os caches do React Query antes de fazer logout
    queryClient.clear()
    logout()
    navigate('/login')
  }

  const menuItems = [
    { to: '/app/dashboard', icon: Home, label: 'Painel' },
    { to: '/app/bills', icon: FileText, label: 'Boletos' },
    { to: '/app/finances', icon: DollarSign, label: 'Finanças' },
    { to: '/app/bills/add', icon: Upload, label: 'Adicionar' },
    { to: '/app/payments', icon: Calendar, label: 'Pagamentos' },
    { to: '/app/installments', icon: CreditCard, label: 'Parcelados' },
    { to: '/app/savings-goals', icon: Target, label: 'Metas' },
    { to: '/app/investments', icon: TrendingUp, label: 'Investimentos' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <Chatbot />
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/app/dashboard" className="flex items-center px-2 sm:px-4 text-lg sm:text-xl font-bold text-gray-900 hover:text-gray-700 transition-colors">
                <span className="text-gray-900">Economize</span>
                <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">IA</span>
              </Link>
              
              {/* Menu Desktop */}
              <div className="hidden lg:flex space-x-1 ml-8">
                {menuItems.map((item) => {
                  const Icon = item.icon
                  return (
                    <Link
                      key={item.to}
                      to={item.to}
                      className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500"
                      aria-label={item.label}
                    >
                      <Icon className="w-4 h-4 mr-2" aria-hidden="true" />
                      {item.label}
                    </Link>
                  )
                })}
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {/* Botão Sair Desktop */}
              <button
                onClick={handleLogout}
                className="hidden sm:flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Sair
              </button>
              
              {/* Botão Hambúrguer Mobile */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden p-2 text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
                aria-label="Menu"
              >
                {mobileMenuOpen ? (
                  <X className="w-6 h-6" />
                ) : (
                  <Menu className="w-6 h-6" />
                )}
              </button>
            </div>
          </div>
        </div>
        
        {/* Menu Mobile */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-gray-200 bg-white">
            <div className="px-2 pt-2 pb-3 space-y-1">
              {menuItems.map((item) => {
                const Icon = item.icon
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center px-3 py-2 text-base font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 min-h-[44px]"
                    aria-label={item.label}
                  >
                    <Icon className="w-5 h-5 mr-3" aria-hidden="true" />
                    {item.label}
                  </Link>
                )
              })}
              <button
                onClick={() => {
                  handleLogout()
                  setMobileMenuOpen(false)
                }}
                className="w-full flex items-center px-3 py-2 text-base font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
              >
                <LogOut className="w-5 h-5 mr-3" />
                Sair
              </button>
            </div>
          </div>
        )}
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
        <Outlet />
      </main>
    </div>
  )
}

