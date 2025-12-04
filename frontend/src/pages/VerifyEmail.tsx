import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import api from '../services/api'
import { CheckCircle, XCircle, Mail, ArrowLeft } from 'lucide-react'

export default function VerifyEmail() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [token, setToken] = useState<string | null>(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [verified, setVerified] = useState(false)

  useEffect(() => {
    const tokenFromUrl = searchParams.get('token')
    if (tokenFromUrl) {
      setToken(tokenFromUrl)
      handleVerify(tokenFromUrl)
    } else {
      setError('Token de verificação não encontrado na URL.')
    }
  }, [searchParams])

  const handleVerify = async (verifyToken: string) => {
    setLoading(true)
    setError('')
    setMessage('')

    try {
      const response = await api.post('/auth/verify-email', { token: verifyToken })
      setMessage(response.data.message)
      setVerified(true)
      setTimeout(() => {
        navigate('/login')
      }, 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao verificar email. O token pode ser inválido ou expirado.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-lg border border-gray-200">
        {verified ? (
          <>
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
                <CheckCircle className="h-10 w-10 text-green-600" />
              </div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                Email Verificado!
              </h2>
              <p className="text-gray-600 mb-6">
                {message || 'Seu email foi verificado com sucesso!'}
              </p>
              <p className="text-sm text-gray-500 mb-6">
                Redirecionando para o login em alguns segundos...
              </p>
              <Link
                to="/login"
                className="inline-flex items-center px-6 py-3 bg-gray-900 text-white rounded-md hover:bg-gray-800 font-semibold text-sm transition-colors"
              >
                Ir para Login
              </Link>
            </div>
          </>
        ) : error ? (
          <>
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100 mb-4">
                <XCircle className="h-10 w-10 text-red-600" />
              </div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                Erro na Verificação
              </h2>
              <p className="text-gray-600 mb-6">
                {error}
              </p>
              <div className="space-y-3">
                <Link
                  to="/login"
                  className="inline-flex items-center px-6 py-3 bg-gray-900 text-white rounded-md hover:bg-gray-800 font-semibold text-sm transition-colors"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Voltar para Login
                </Link>
                <p className="text-sm text-gray-500">
                  Precisa de um novo link? Entre em contato conosco.
                </p>
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-blue-100 mb-4">
                <Mail className="h-10 w-10 text-blue-600" />
              </div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                Verificando Email...
              </h2>
              <p className="text-gray-600 mb-6">
                Aguarde enquanto verificamos seu email.
              </p>
              {loading && (
                <div className="flex justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

