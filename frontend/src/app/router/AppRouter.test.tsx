import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { AuthContextValue } from '../providers/auth-context'
import { AppRouter } from './AppRouter'

const mockUseAuth = vi.fn<() => AuthContextValue>()

vi.mock('../providers/auth-context', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../providers/auth-context')>()
  return { ...actual, useAuth: () => mockUseAuth() }
})

function setPath(path: string) {
  window.history.pushState({}, '', path)
}

describe('AppRouter — guarda de rota', () => {
  afterEach(() => {
    mockUseAuth.mockReset()
  })

  it('redireciona para /login quando não autenticado', () => {
    setPath('/seller')
    mockUseAuth.mockReturnValue({
      status: 'unauthenticated',
      user: null,
      login: vi.fn(),
      logout: vi.fn(),
    })

    render(<AppRouter />)

    expect(screen.getByRole('heading', { name: 'Market Hub' })).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
  })

  it('redireciona para a home do papel quando autenticado', () => {
    setPath('/')
    mockUseAuth.mockReturnValue({
      status: 'authenticated',
      user: { id: '1', email: 'seller@x.test', name: 'Loja A', role: 'seller', seller_id: '1' },
      login: vi.fn(),
      logout: vi.fn(),
    })

    render(<AppRouter />)

    expect(screen.getByText(/listagem de Orders/)).toBeInTheDocument()
  })
})
