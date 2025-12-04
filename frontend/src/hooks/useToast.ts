import { useContext } from 'react'
import { ToastContext } from '../components/ToastContainer'

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    // Fallback se ToastContext não estiver disponível
    return {
      showToast: (message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info') => {
        console.log(`[Toast] ${type}: ${message}`)
      }
    }
  }
  return context
}

