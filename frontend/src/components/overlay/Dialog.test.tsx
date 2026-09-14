import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { Dialog } from './Dialog'

function Harness({ onClose }: { onClose: () => void }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button type="button" onClick={() => setOpen(true)}>
        Abrir
      </button>
      <Dialog
        open={open}
        title="Confirmar"
        description="Isto não pode ser desfeito."
        onClose={() => {
          setOpen(false)
          onClose()
        }}
      >
        <button type="button">Confirmar ação</button>
      </Dialog>
    </>
  )
}

describe('Dialog', () => {
  it('is announced as a modal labelled by its title', () => {
    render(
      <Dialog open title="Confirmar" description="Isto não pode ser desfeito." onClose={vi.fn()}>
        <button type="button">Confirmar ação</button>
      </Dialog>,
    )

    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(dialog).toHaveAccessibleName('Confirmar')
    expect(dialog).toHaveAccessibleDescription('Isto não pode ser desfeito.')
  })

  it('moves focus into the dialog and returns it to the trigger on close', async () => {
    const user = userEvent.setup()
    render(<Harness onClose={vi.fn()} />)
    const trigger = screen.getByRole('button', { name: 'Abrir' })

    await user.click(trigger)
    expect(screen.getByRole('button', { name: 'Confirmar ação' })).toHaveFocus()

    await user.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(trigger).toHaveFocus()
  })

  it('closes on Escape', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    render(<Harness onClose={onClose} />)

    await user.click(screen.getByRole('button', { name: 'Abrir' }))
    await user.keyboard('{Escape}')

    expect(onClose).toHaveBeenCalledOnce()
  })
})
