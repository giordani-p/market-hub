import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '../../app/providers/auth-context'
import { ApiRequestError } from '../../lib/api/client'
import { LoginPage } from './LoginPage'

function renderWithAuth(overrides: Partial<AuthContextValue>) {
  const value: AuthContextValue = {
    status: 'unauthenticated',
    user: null,
    login: vi.fn(),
    logout: vi.fn(),
    ...overrides,
  }
  render(
    <AuthContext.Provider value={value}>
      <LoginPage />
    </AuthContext.Provider>,
  )
  return value
}

describe('LoginPage', () => {
  it('submits the typed credentials', async () => {
    const login = vi.fn().mockResolvedValue(undefined)
    renderWithAuth({ login })
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('Email'), 'seller@marketplace.test')
    await user.type(screen.getByLabelText('Senha'), 'secret')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    await waitFor(() => {
      expect(login).toHaveBeenCalledWith('seller@marketplace.test', 'secret')
    })
  })

  it('shows a friendly message for invalid credentials', async () => {
    const login = vi
      .fn()
      .mockRejectedValue(
        new ApiRequestError({ status: 401, code: 'unauthorized', message: 'Invalid credentials' }),
      )
    renderWithAuth({ login })
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('Email'), 'seller@marketplace.test')
    await user.type(screen.getByLabelText('Senha'), 'wrong')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Email ou senha inválidos.')
  })
})
