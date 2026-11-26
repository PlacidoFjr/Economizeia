import { createContext, useContext, useEffect, useMemo, useState, ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import api from '../services/api'

interface User {
  id: string
  email: string
  name: string
  email_verified?: boolean
  is_active?: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<any>
  logout: () => Promise<void>
  isAuthenticated: boolean
  isAuthLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

function clearAuthTokens() {
  sessionStorage.removeItem('access_token')
  sessionStorage.removeItem('refresh_token')
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [user, setUser] = useState<User | null>(null)
  const [isAuthLoading, setIsAuthLoading] = useState(true)

  const loadCurrentUser = async () => {
    const response = await api.get('/auth/me')
    setUser(response.data)
  }

  useEffect(() => {
    if (!sessionStorage.getItem('access_token')) {
      setIsAuthLoading(false)
      return
    }
    loadCurrentUser()
      .catch(() => {
        clearAuthTokens()
        setUser(null)
      })
      .finally(() => setIsAuthLoading(false))
  }, [])

  const login = async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password })
    const { access_token, refresh_token } = response.data
    if (!access_token || !refresh_token) {
      throw new Error('O servidor não retornou os tokens de autenticação.')
    }
    sessionStorage.setItem('access_token', access_token)
    sessionStorage.setItem('refresh_token', refresh_token)
    try {
      await loadCurrentUser()
    } catch (error) {
      clearAuthTokens()
      setUser(null)
      throw error
    }
  }

  const register = async (name: string, email: string, password: string) => {
    const response = await api.post('/auth/register', { name, email, password })
    clearAuthTokens()
    return response.data
  }

  const logout = async () => {
    clearAuthTokens()
    queryClient.clear()
    setUser(null)
  }

  const value = useMemo<AuthContextType>(
    () => ({
      user,
      token: sessionStorage.getItem('access_token'),
      login,
      register,
      logout,
      isAuthenticated: !!user,
      isAuthLoading,
    }),
    [user, isAuthLoading]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
