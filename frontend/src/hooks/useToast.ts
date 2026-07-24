import { useContext } from 'react'
import { ToastContext } from '../components/ToastContainer'

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    // Fallback se ToastContext não estiver disponível
    return {
      showToast: () => undefined
    }
  }
  return context
}

