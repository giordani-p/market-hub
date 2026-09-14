import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext } from '../providers/auth-context'
import type { AuthUser } from '../../types/auth'
import { AppLayout } from './AppLayout'

vi.mock('../../features/notifications/NotificationBell', () => ({
  NotificationBell: () => <div>Sino</div>,
}))

function renderShell(user: AuthUser, entry = '/ops/queue') {
  return render(
    <AuthContext.Provider
      value={{ status: 'authenticated', user, login: vi.fn(), logout: vi.fn() }}
    >
      <MemoryRouter initialEntries={[entry]}>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/ops/queue" element={<h1 id="page-title">Fila de atendimento</h1>} />
            <Route path="/catalog" element={<h1 id="page-title">Catálogo</h1>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  )
}

const ops: AuthUser = {
  id: '1',
  email: 'ops@x.test',
  name: 'Ana Souza',
  role: 'ops',
  seller_id: null,
}

const buyer: AuthUser = {
  id: '2',
  email: 'buyer@x.test',
  name: 'Bruno Lima',
  role: 'buyer',
  seller_id: null,
}

describe('AppLayout', () => {
  it('offers a skip link that points at the main landmark', () => {
    renderShell(ops)

    expect(screen.getByRole('link', { name: 'Ir para o conteúdo' })).toHaveAttribute(
      'href',
      '#main-content',
    )
    expect(screen.getByRole('main')).toHaveAttribute('id', 'main-content')
  })

  it('marks the current destination in the navigation', () => {
    renderShell(ops)

    expect(screen.getByRole('link', { name: 'Fila de atendimento' })).toHaveAttribute(
      'aria-current',
      'page',
    )
    expect(screen.getByRole('link', { name: 'Catálogo' })).not.toHaveAttribute('aria-current')
  })

  it('opens the navigation drawer for the operational roles', async () => {
    const user = userEvent.setup()
    renderShell(ops)

    const toggle = screen.getByRole('button', { name: 'Abrir navegação' })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')

    await user.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'true')

    await user.keyboard('{Escape}')
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
  })

  it('gives the buyer a horizontal navigation, without the drawer toggle', () => {
    renderShell(buyer, '/catalog')

    expect(screen.queryByRole('button', { name: 'Abrir navegação' })).not.toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Navegação principal' })).toBeInTheDocument()
  })

  it('sends a free-text search from the header to the catalog', async () => {
    const user = userEvent.setup()
    renderShell(buyer, '/ops/queue')

    await user.type(screen.getByRole('searchbox', { name: 'Buscar' }), 'tenis{Enter}')

    expect(screen.getByRole('heading', { name: 'Catálogo' })).toBeInTheDocument()
  })
})
