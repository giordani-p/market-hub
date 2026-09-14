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
  it('lets the reader reveal and hide the typed password', async () => {
    renderWithAuth({})
    const user = userEvent.setup()
    const password = screen.getByLabelText('Senha')

    await user.type(password, 'secret')
    expect(password).toHaveAttribute('type', 'password')

    await user.click(screen.getByRole('button', { name: 'Mostrar senha' }))
    expect(password).toHaveAttribute('type', 'text')

    await user.click(screen.getByRole('button', { name: 'Ocultar senha' }))
    expect(password).toHaveAttribute('type', 'password')
  })
  it('asks for the missing fields in Portuguese instead of calling the API', async () => {
    const login = vi.fn()
    renderWithAuth({ login })
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(login).not.toHaveBeenCalled()
    expect(screen.getByText('Informe seu email.')).toBeInTheDocument()
    expect(screen.getByText('Informe sua senha.')).toBeInTheDocument()
  })

  it('does not leak the raw API message for an unexpected failure', async () => {
    const login = vi.fn().mockRejectedValue(
      new ApiRequestError({
        status: 422,
        code: 'validation_error',
        message: 'value is not a valid email address',
      }),
    )
    renderWithAuth({ login })
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('Email'), 'seller@marketplace.test')
    await user.type(screen.getByLabelText('Senha'), 'secret')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Não foi possível entrar agora.')
    expect(alert).not.toHaveTextContent('valid email address')
  })
})
