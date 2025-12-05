import axios from 'axios'

// Usar variável de ambiente ou fallback para desenvolvimento
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

// Aviso se a URL não estiver configurada em produção
if (import.meta.env.PROD && !import.meta.env.VITE_API_URL) {
  console.error('⚠️ VITE_API_URL não configurada! Configure no Vercel → Settings → Environment Variables')
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 segundos
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
    // Tratamento de timeout ou erro de conexão
    if (error.code === 'ECONNABORTED' || error.message === 'Network Error' || !error.response) {
      const errorMessage = API_BASE_URL.startsWith('http') 
        ? 'Não foi possível conectar ao servidor. Verifique sua conexão.'
        : 'URL da API não configurada. Verifique as variáveis de ambiente.'
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

