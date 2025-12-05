import axios from 'axios'

// Usar variável de ambiente ou fallback para desenvolvimento
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

// Log da URL da API para debug
console.log('🔧 API Base URL:', API_BASE_URL)
console.log('🔧 Environment:', import.meta.env.MODE)
console.log('🔧 VITE_API_URL:', import.meta.env.VITE_API_URL)

// Aviso se a URL não estiver configurada em produção
if (import.meta.env.PROD && !import.meta.env.VITE_API_URL) {
  console.error('⚠️ VITE_API_URL não configurada! Configure no Vercel → Settings → Environment Variables')
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 90000, // 90 segundos (aumentado para dar tempo ao SMTP)
})

// Request interceptor to add token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Log detalhado do erro para debug
    console.error('❌ Erro na API:', {
      code: error.code,
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      url: error.config?.url,
      baseURL: error.config?.baseURL,
    })

    // Tratamento de timeout ou erro de conexão
    if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK' || error.code === 'ERR_INTERNET_DISCONNECTED' || error.message === 'Network Error' || !error.response) {
      // Verificar se está offline
      if (!navigator.onLine) {
        const errorMessage = 'Sem conexão com a internet. Verifique sua conexão e tente novamente.'
        console.error('❌ Sem conexão:', errorMessage)
        return Promise.reject(new Error(errorMessage))
      }
      
      // Se está online mas não consegue conectar, pode ser problema no servidor ou URL incorreta
      let errorMessage = ''
      if (!API_BASE_URL || API_BASE_URL === '/api/v1') {
        errorMessage = 'URL da API não configurada. O backend não está acessível. Verifique se VITE_API_URL está configurado no Vercel.'
      } else if (API_BASE_URL.startsWith('http')) {
        errorMessage = `Não foi possível conectar ao servidor (${API_BASE_URL}). O backend pode estar offline ou a URL está incorreta. Verifique sua conexão e tente novamente.`
      } else {
        errorMessage = 'URL da API inválida. Configure VITE_API_URL no Vercel → Settings → Environment Variables com a URL do backend (ex: https://seu-backend.railway.app).'
      }
      console.error('❌ Erro de conexão:', {
        errorMessage,
        API_BASE_URL,
        code: error.code,
        message: error.message,
        online: navigator.onLine
      })
      return Promise.reject(new Error(errorMessage))
    }

    if (error.response?.status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })
          const { access_token } = response.data
          localStorage.setItem('access_token', access_token)
          error.config.headers.Authorization = `Bearer ${access_token}`
          return api.request(error.config)
        } catch (refreshError) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          // Só redirecionar se não estiver na página inicial ou de login/register
          const currentPath = window.location.pathname
          if (currentPath !== '/' && !currentPath.startsWith('/login') && !currentPath.startsWith('/register')) {
            window.location.href = '/login'
          }
        }
      } else {
        // Só redirecionar se não estiver na página inicial ou de login/register
        const currentPath = window.location.pathname
        if (currentPath !== '/' && !currentPath.startsWith('/login') && !currentPath.startsWith('/register')) {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api

