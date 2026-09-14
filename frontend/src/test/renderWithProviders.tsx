import { render, type RenderOptions, type RenderResult } from '@testing-library/react'
import type { ReactElement, ReactNode } from 'react'
import { ToastProvider } from '../components/overlay/ToastProvider'

/**
 * Envolve a arvore nos providers de aplicacao que qualquer tela assume
 * existir. Hoje so o Toast; auth e router continuam explicitos em cada
 * teste, porque variam por caso.
 */
export function renderWithProviders(ui: ReactElement, options?: RenderOptions): RenderResult {
  function Wrapper({ children }: { children: ReactNode }) {
    return <ToastProvider>{children}</ToastProvider>
  }
  return render(ui, { wrapper: Wrapper, ...options })
}
