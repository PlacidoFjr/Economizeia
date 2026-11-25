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

// The Render backend authenticates with JWT bearer tokens, not auth cookies.
api.interceptors.request.use((config) => {
  const accessToken = sessionStorage.getItem('access_token')
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

let refreshPromise: Promise<string> | null = null

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined
    const isAuthAction = /\/auth\/(login|register|refresh|forgot-password|reset-password)/.test(originalRequest?.url || '')

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !isAuthAction &&
      sessionStorage.getItem('refresh_token')
    ) {
      originalRequest._retry = true
      try {
        if (!refreshPromise) {
          refreshPromise = axios.post(
            `${API_BASE_URL}/auth/refresh`,
            { refresh_token: sessionStorage.getItem('refresh_token') },
            { withCredentials: true }
          ).then((res) => {
            const { access_token, refresh_token } = res.data
            if (!access_token || !refresh_token) throw new Error('Invalid refresh response')
            sessionStorage.setItem('access_token', access_token)
            sessionStorage.setItem('refresh_token', refresh_token)
            return access_token as string
          }).finally(() => { refreshPromise = null })
        }
        const token = await refreshPromise
        originalRequest.headers.Authorization = `Bearer ${token}`
        return api.request(originalRequest)
      } catch {
        sessionStorage.removeItem('access_token')
        sessionStorage.removeItem('refresh_token')
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
