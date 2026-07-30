import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'motion/react'
import { ArrowLeft, CheckCircle, Lock, Mail, User } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../hooks/useToast'
import ThemeToggle from '../components/ThemeToggle'
import AuthVisualPanel from '../components/AuthVisualPanel'
import AuthInput from '../components/AuthInput'

export default function Register() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const { register } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()

  const getRegisterErrorMessage = (err: any) => {
    const backendMessage = err.response?.data?.detail || err.message || ''
    const statusCode = err.response?.status

    if (backendMessage.includes('já cadastrado') || backendMessage.includes('já existe') || backendMessage.includes('Email já')) {
      return 'Este email já está cadastrado. Tente fazer login ou use outro email.'
    }
    if (backendMessage.includes('inválido') || backendMessage.includes('invalid')) {
      return 'Email inválido. Verifique se o email está correto.'
    }
    if ((backendMessage.includes('senha') && backendMessage.includes('curta')) || (backendMessage.includes('password') && backendMessage.includes('short'))) {
      return 'A senha deve ter pelo menos 8 caracteres.'
    }
    if (
      backendMessage.includes('conectar') ||
      backendMessage.includes('timeout') ||
      backendMessage.includes('Failed to fetch') ||
      backendMessage.includes('Network Error') ||
      backendMessage.includes('API não configurada') ||
      err.code === 'ECONNABORTED' ||
      err.code === 'ERR_NETWORK'
    ) {
      return 'Não foi possível conectar ao servidor. Confira a URL da API, CORS do Render ou aguarde o backend acordar.'
    }
    if (statusCode === 400) return backendMessage || 'Dados inválidos. Verifique os campos.'
    if (statusCode === 409) return 'Este email já está cadastrado. Tente fazer login.'
    if (statusCode === 500) return 'Erro no servidor. Tente novamente em alguns instantes.'
    if (backendMessage && !backendMessage.includes('Erro') && !backendMessage.includes('Error')) return backendMessage

    return 'Erro ao criar conta. Tente novamente.'
  }

  const checkBackendConnection = async () => {
    const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'
    if (!API_BASE_URL.startsWith('http')) return

    const baseUrl = API_BASE_URL.replace('/api/v1', '').replace(/\/$/, '')
    try {
      const response = await fetch(`${baseUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(8000),
      })
      if (!response.ok) {
        throw new Error('Backend não está respondendo corretamente')
      }
    } catch {
      throw new Error('Não foi possível conectar ao servidor. Confira a URL da API, CORS do Render ou aguarde o backend acordar.')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSuccess(false)
    setLoading(true)

    if (!navigator.onLine) {
      setLoading(false)
      showToast('Sem conexão com a internet. Verifique sua conexão e tente novamente.', 'error', 8000)
      return
    }

    try {
      await checkBackendConnection()
      const response = await register(name, email, password)

      if (response?.requires_verification) {
        setSuccess(true)
        setSuccessMessage(response.message || 'Conta criada com sucesso! Verifique seu email para confirmar o registro.')
        showToast('Conta criada! Verifique seu email para confirmar.', 'success', 8000)
      } else {
        showToast('Registro realizado com sucesso!', 'success')
        navigate('/app/dashboard')
      }
    } catch (err: any) {
      console.error('Erro no registro:', err)
      showToast(getRegisterErrorMessage(err), 'error', 8000)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-white dark:bg-slate-950">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.32, ease: 'easeOut' }}
        className="grid min-h-screen w-full overflow-hidden bg-white dark:bg-slate-900 lg:grid-cols-[minmax(480px,0.9fr)_1.1fr]"
      >
        <div className="flex min-h-screen flex-col justify-center bg-white px-6 py-8 dark:bg-slate-900 sm:px-10 lg:px-16">
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

          <div className="mx-auto mb-6 w-full max-w-md text-center">
            <div className="mb-4 text-3xl font-bold tracking-tight text-slate-950 dark:text-white">
              Economize<span className="text-cyan-600 dark:text-cyan-400">IA</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-950 dark:text-white">Criar sua conta</h1>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">Comece a organizar suas finanças.</p>
          </div>

          {success && (
            <div className="mb-5 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-900 dark:bg-green-950/40">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 rounded-lg bg-green-100 p-2 dark:bg-green-900">
                  <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-300" />
                </div>
                <div className="flex-1">
                  <h3 className="mb-1 text-sm font-bold text-green-900 dark:text-green-100">Conta criada com sucesso!</h3>
                  <p className="text-sm text-green-700 dark:text-green-200">{successMessage}</p>
                  <p className="mt-2 text-sm text-green-700 dark:text-green-200">
                    Enviamos um email de verificação para <strong>{email}</strong>.
                  </p>
                  <Link to="/login" className="mt-3 inline-flex text-sm font-semibold text-green-800 underline hover:text-green-950 dark:text-green-100">
                    Já confirmou? Fazer login
                  </Link>
                </div>
              </div>
            </div>
          )}

          <form className="mx-auto w-full max-w-md space-y-4" onSubmit={handleSubmit}>
            <div>
              <AuthInput
                id="name"
                name="name"
                type="text"
                label="Nome completo"
                required
                autoComplete="name"
                placeholder="Seu nome completo"
                value={name}
                onChange={(e) => setName(e.target.value)}
                icon={<User className="h-5 w-5" />}
              />
            </div>

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
                autoComplete="new-password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                icon={<Lock className="h-5 w-5" />}
              />
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Mínimo de 8 caracteres recomendado</p>
            </div>

            <div className="flex items-start">
              <input
                id="terms"
                name="terms"
                type="checkbox"
                required
                className="mt-1 h-4 w-4 rounded border-slate-400 bg-white text-slate-950 focus:ring-slate-500 dark:border-slate-500 dark:bg-slate-950 dark:ring-offset-slate-900"
              />
              <label htmlFor="terms" className="ml-3 text-sm leading-relaxed text-slate-600 dark:text-slate-200">
                Eu concordo com os{' '}
                <Link to="/termos" className="font-semibold text-slate-950 underline underline-offset-2 dark:text-white" target="_blank">
                  Termos de Uso
                </Link>{' '}
                e{' '}
                <Link to="/privacidade" className="font-semibold text-slate-950 underline underline-offset-2 dark:text-white" target="_blank">
                  Política de Privacidade
                </Link>
              </label>
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
                  Criando conta...
                </>
              ) : (
                'Criar conta'
              )}
            </motion.button>

            <div className="pt-1 text-center text-sm text-slate-600 dark:text-slate-300">
              Já tem conta?{' '}
              <Link to="/login" className="font-semibold text-slate-950 underline transition-colors hover:text-slate-700 dark:text-white dark:hover:text-slate-200">
                Faça login
              </Link>
            </div>
          </form>
        </div>
        <AuthVisualPanel />
      </motion.div>
    </div>
  )
}
