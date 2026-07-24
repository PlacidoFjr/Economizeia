import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 90000,
})

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        await axios.post(`${API_BASE_URL}/auth/refresh`, {}, { withCredentials: true })
        return api.request(originalRequest)
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        const currentPath = window.location.pathname
        if (currentPath !== '/' && !currentPath.startsWith('/login') && !currentPath.startsWith('/register')) {
          window.location.href = '/login'
        }
      }
    }

    if (!error.response) {
      const message = navigator.onLine
        ? 'Não foi possível conectar ao servidor. Tente novamente em alguns instantes.'
        : 'Sem conexão com a internet. Verifique sua conexão e tente novamente.'
      return Promise.reject(new Error(message))
    }

    return Promise.reject(error)
  }
)

export default api
