import { createContext, useContext, useEffect, useMemo, useState, ReactNode } from 'react'
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

function clearLegacyTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  delete api.defaults.headers.common.Authorization
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isAuthLoading, setIsAuthLoading] = useState(true)

  const loadCurrentUser = async () => {
    const response = await api.get('/auth/me')
    setUser(response.data)
  }

  useEffect(() => {
    clearLegacyTokens()
    loadCurrentUser()
      .catch(() => setUser(null))
      .finally(() => setIsAuthLoading(false))
  }, [])

  const login = async (email: string, password: string) => {
    await api.post('/auth/login', { email, password })
    clearLegacyTokens()
    await loadCurrentUser()
  }

  const register = async (name: string, email: string, password: string) => {
    const response = await api.post('/auth/register', { name, email, password })
    clearLegacyTokens()
    return response.data
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout')
    } finally {
      clearLegacyTokens()
      setUser(null)
    }
  }

  const value = useMemo<AuthContextType>(
    () => ({
      user,
      token: null,
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
