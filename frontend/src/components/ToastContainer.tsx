import React, { useState, useCallback } from 'react'
import Toast, { ToastType } from './Toast'

interface ToastContainerProps {
  children: React.ReactNode
}

export interface ToastContextType {
  showToast: (message: string, type: ToastType, duration?: number) => void
}

export const ToastContext = React.createContext<ToastContextType | null>(null)

export default function ToastContainer({ children }: ToastContainerProps) {
  const [toasts, setToasts] = useState<Array<{ id: string; message: string; type: ToastType; duration?: number }>>([])

  const showToast = useCallback((message: string, type: ToastType, duration?: number) => {
    const id = Date.now().toString() + Math.random().toString(36).substr(2, 9)
    setToasts((prev) => [...prev, { id, message, type, duration }])
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed top-4 left-4 right-4 sm:left-auto sm:right-4 z-[100] flex flex-col space-y-2 max-w-full sm:max-w-md">
        {toasts.map((toast) => (
          <Toast key={toast.id} toast={toast} onClose={removeToast} />
        ))}
      </div>
    </ToastContext.Provider>
  )
}

