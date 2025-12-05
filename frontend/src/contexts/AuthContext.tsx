import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import api from '../services/api'

interface User {
  id: string
  email: string
  name: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<any>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(
    localStorage.getItem('access_token')
  )

  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      // Optionally fetch user data
    }
  }, [token])

  const login = async (email: string, password: string) => {
    try {
      console.log('🔐 Tentando fazer login...')
      console.log('🔐 URL da API:', api.defaults.baseURL)
      const response = await api.post('/auth/login', { email, password })
      console.log('✅ Login bem-sucedido:', response.data)
      const { access_token, refresh_token } = response.data
      setToken(access_token)
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      // Fetch user data if needed
    } catch (error: any) {
      console.error('❌ Erro no login (AuthContext):', error)
      // Re-throw para o componente tratar
      throw error
    }
  }

  const register = async (name: string, email: string, password: string) => {
    try {
      console.log('📝 Tentando registrar usuário...')
      console.log('📝 URL da API:', api.defaults.baseURL)
      const response = await api.post('/auth/register', { name, email, password })
      console.log('✅ Registro bem-sucedido:', response.data)
      // Se não requer verificação, fazer login automático
      if (response.data.access_token) {
        const { access_token, refresh_token } = response.data
        setToken(access_token)
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('refresh_token', refresh_token)
        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      }
      // Retornar resposta para o componente decidir o que fazer
      return response.data
    } catch (error: any) {
      console.error('❌ Erro no registro (AuthContext):', error)
      throw error
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    delete api.defaults.headers.common['Authorization']
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        register,
        logout,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

