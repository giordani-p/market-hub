import { createContext, useContext } from 'react'

export type ToastTone = 'success' | 'error'

export interface ToastOptions {
  message: string
  tone?: ToastTone
}

export interface ToastContextValue {
  showToast: (options: ToastOptions) => void
}

export const ToastContext = createContext<ToastContextValue | null>(null)

/** Feedback de acao concluida. Antes toda mutacao terminava em silencio. */
export function useToast(): ToastContextValue {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast precisa estar dentro de ToastProvider.')
  }
  return context
}
