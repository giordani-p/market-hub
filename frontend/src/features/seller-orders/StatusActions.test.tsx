import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { StatusActions } from './StatusActions'

const { advanceOrderItemStatus, cancelOrderItem } = vi.hoisted(() => ({
  advanceOrderItemStatus: vi.fn(),
  cancelOrderItem: vi.fn(),
}))

vi.mock('./api', () => ({ advanceOrderItemStatus, cancelOrderItem }))

describe('StatusActions', () => {
  afterEach(() => {
    advanceOrderItemStatus.mockReset()
    cancelOrderItem.mockReset()
  })

  it('offers to advance and to cancel a placed item', () => {
    render(<StatusActions itemId="item-1" status="placed" onChanged={vi.fn()} />)

    expect(screen.getByRole('button', { name: 'Avançar para Em preparação' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancelar pedido' })).toBeInTheDocument()
  })

  it('hides both actions once delivered', () => {
    render(<StatusActions itemId="item-1" status="delivered" onChanged={vi.fn()} />)

    expect(screen.queryByRole('button', { name: /Avançar/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Cancelar pedido' })).not.toBeInTheDocument()
  })

  it('shows a note instead of the stepper when cancelled', () => {
    render(<StatusActions itemId="item-1" status="cancelled" onChanged={vi.fn()} />)

    expect(screen.getByText('Este item foi cancelado.')).toBeInTheDocument()
  })

  it('advances the status and notifies the parent', async () => {
    advanceOrderItemStatus.mockResolvedValue(undefined)
    const onChanged = vi.fn()
    render(<StatusActions itemId="item-1" status="placed" onChanged={onChanged} />)
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: 'Avançar para Em preparação' }))

    expect(advanceOrderItemStatus).toHaveBeenCalledWith('item-1', 'preparing')
    expect(onChanged).toHaveBeenCalledOnce()
  })

  it('asks for confirmation before cancelling', async () => {
    cancelOrderItem.mockResolvedValue(undefined)
    const onChanged = vi.fn()
    render(<StatusActions itemId="item-1" status="placed" onChanged={onChanged} />)
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: 'Cancelar pedido' }))
    expect(cancelOrderItem).not.toHaveBeenCalled()

    await user.click(screen.getByRole('button', { name: 'Confirmar cancelamento' }))

    expect(cancelOrderItem).toHaveBeenCalledWith('item-1')
    expect(onChanged).toHaveBeenCalledOnce()
  })
})
