import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { motion } from 'motion/react'
import { ArrowLeft, Lock, Mail } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../hooks/useToast'
import ThemeToggle from '../components/ThemeToggle'
import AuthVisualPanel from '../components/AuthVisualPanel'
import AuthInput from '../components/AuthInput'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const navigate = useNavigate()

  const getLoginErrorMessage = (err: any) => {
    const backendMessage = err.response?.data?.detail || err.message || ''
    const statusCode = err.response?.status

    if (backendMessage.includes('não cadastrado') || backendMessage.includes('Email não cadastrado')) {
      return 'Email não cadastrado. Verifique o email ou crie uma conta.'
    }
    if (backendMessage.includes('não verificado') || backendMessage.includes('verificar') || backendMessage.includes('Email não verificado')) {
      return 'Seu email ainda não foi verificado. Verifique sua caixa de entrada e clique no link de confirmação que enviamos.'
    }
    if (backendMessage.includes('Senha incorreta') || backendMessage.includes('senha incorreta')) {
      return 'Senha incorreta. Verifique sua senha e tente novamente.'
    }
    if (backendMessage.includes('incorretos') || backendMessage.includes('Email ou senha')) {
      return 'Email ou senha incorretos. Verifique suas credenciais e tente novamente.'
    }
    if (backendMessage.includes('inativa') || backendMessage.includes('inativo')) {
      return 'Sua conta está inativa. Entre em contato com o suporte para mais informações.'
    }
    if (
      backendMessage.includes('conectar') ||
      backendMessage.includes('timeout') ||
      backendMessage.includes('Network Error') ||
      backendMessage.includes('API não configurada') ||
      err.code === 'ECONNABORTED' ||
      err.code === 'ERR_NETWORK'
    ) {
      return 'Sem conexão com a internet ou servidor indisponível. Verifique sua conexão e tente novamente.'
    }
    if (statusCode === 401) return 'Senha incorreta. Verifique sua senha e tente novamente.'
    if (statusCode === 403) return 'Acesso negado. Verifique se seu email foi confirmado ou entre em contato com o suporte.'
    if (statusCode === 404) return 'Email não cadastrado. Verifique o email ou crie uma conta.'
    if (statusCode === 500) return 'Erro no servidor. Tente novamente em alguns instantes.'
    if (backendMessage && !backendMessage.includes('Erro')) return backendMessage

    return 'Erro ao fazer login. Tente novamente.'
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    if (!navigator.onLine) {
      setLoading(false)
      showToast('Sem conexão com a internet. Verifique sua conexão e tente novamente.', 'error', 8000)
      return
    }

    try {
      await login(email, password)
      queryClient.clear()
      showToast('Login realizado com sucesso!', 'success')
      navigate('/app/dashboard')
    } catch (err: any) {
      console.error('Erro no login:', err)
      showToast(getLoginErrorMessage(err), 'error', 8000)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center overflow-y-auto bg-slate-100 px-4 py-8 dark:bg-slate-950 sm:px-6 lg:py-10">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.32, ease: 'easeOut' }}
        className="grid w-full max-w-5xl overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl shadow-slate-300/50 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/20 lg:min-h-[580px] lg:grid-cols-[0.96fr_1.04fr]"
      >
        <div className="flex flex-col justify-center bg-white px-6 py-8 dark:bg-slate-900 sm:px-10 lg:px-12">
          <div className="mb-6 flex items-center justify-between gap-3">
            <button
              onClick={() => navigate('/')}
              className="group flex items-center text-sm font-medium text-slate-600 transition-colors hover:text-slate-950 dark:text-slate-300 dark:hover:text-white"
            >
              <ArrowLeft className="mr-2 h-4 w-4 transition-transform group-hover:-translate-x-1" />
              Voltar
            </button>
            <ThemeToggle />
          </div>

          <div className="mx-auto mb-7 w-full max-w-md text-center">
            <div className="mb-5 text-3xl font-bold tracking-tight text-slate-950 dark:text-white">
              Economize<span className="text-cyan-600 dark:text-cyan-400">IA</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-950 dark:text-white">Entrar na sua conta</h1>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">Continue acompanhando suas finanças.</p>
          </div>

          <form className="mx-auto w-full max-w-md space-y-5" onSubmit={handleSubmit}>
            <div>
              <AuthInput
                id="email"
                name="email"
                type="email"
                label="Email"
                required
                autoComplete="email"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                icon={<Mail className="h-5 w-5" />}
              />
            </div>

            <div>
              <AuthInput
                id="password"
                name="password"
                type="password"
                label="Senha"
                required
                autoComplete="current-password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                icon={<Lock className="h-5 w-5" />}
              />
            </div>

            <motion.button
              whileTap={{ scale: 0.99 }}
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center rounded-lg bg-slate-950 px-4 py-3.5 text-base font-semibold text-white shadow-sm transition-colors hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
            >
              {loading ? (
                <>
                  <div className="mr-2 h-5 w-5 animate-spin rounded-full border-b-2 border-current" />
                  Entrando...
                </>
              ) : (
                'Entrar'
              )}
            </motion.button>

            <div className="space-y-3 pt-1 text-center">
              <Link to="/forgot-password" className="block text-sm font-medium text-slate-600 transition-colors hover:text-slate-950 dark:text-slate-300 dark:hover:text-white">
                Esqueci minha senha
              </Link>
              <div className="text-sm text-slate-600 dark:text-slate-300">
                Não tem conta?{' '}
                <Link to="/register" className="font-semibold text-slate-950 underline transition-colors hover:text-slate-700 dark:text-white dark:hover:text-slate-200">
                  Criar conta
                </Link>
              </div>
            </div>
          </form>
        </div>
        <AuthVisualPanel />
      </motion.div>
    </div>
  )
}
