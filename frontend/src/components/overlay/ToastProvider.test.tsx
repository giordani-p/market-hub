import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { useToast } from './toast-context'
import { ToastProvider } from './ToastProvider'

function Trigger() {
  const { showToast } = useToast()
  return (
    <button type="button" onClick={() => showToast({ message: 'Pedido cancelado.' })}>
      Agir
    </button>
  )
}

describe('ToastProvider', () => {
  it('announces the message in a live region', async () => {
    const user = userEvent.setup()
    render(
      <ToastProvider>
        <Trigger />
      </ToastProvider>,
    )

    // A regiao existe desde o inicio: criada junto com a mensagem, o leitor
    // de tela nao anunciaria nada.
    const region = screen.getByRole('status')
    expect(region).toHaveAttribute('aria-live', 'polite')

    await user.click(screen.getByRole('button', { name: 'Agir' }))
    expect(region).toHaveTextContent('Pedido cancelado.')
  })

  it('lets the reader dismiss the message', async () => {
    const user = userEvent.setup()
    render(
      <ToastProvider>
        <Trigger />
      </ToastProvider>,
    )

    await user.click(screen.getByRole('button', { name: 'Agir' }))
    await user.click(screen.getByRole('button', { name: 'Fechar aviso' }))

    expect(screen.queryByText('Pedido cancelado.')).not.toBeInTheDocument()
  })
})
