import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import './ToastProvider.css'

type ToastKind = 'success' | 'error' | 'info'

type Toast = {
  id: number
  kind: ToastKind
  text: string
}

type ToastContextValue = {
  pushToast: (kind: ToastKind, text: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const value = useMemo<ToastContextValue>(() => ({
    pushToast(kind, text) {
      const id = Date.now() + Math.floor(Math.random() * 1000)
      setToasts(prev => [...prev, { id, kind, text }])
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id))
      }, 3200)
    },
  }), [])

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-stack" aria-live="polite" aria-atomic="true">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast toast-${toast.kind}`}>
            {toast.text}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) {
    throw new Error('useToast must be used within ToastProvider')
  }
  return ctx
}
