import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { BuyerCancelActions } from './BuyerCancelActions'

const { cancelOrderItem } = vi.hoisted(() => ({ cancelOrderItem: vi.fn() }))

vi.mock('./api', () => ({ cancelOrderItem }))

describe('BuyerCancelActions', () => {
  afterEach(() => {
    cancelOrderItem.mockReset()
  })

  it('shows the cancel button for placed items', () => {
    render(<BuyerCancelActions itemId="item-1" status="placed" onChanged={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Cancelar item' })).toBeInTheDocument()
  })

  it('hides the cancel button once the item is in transit', () => {
    render(<BuyerCancelActions itemId="item-1" status="in_transit" onChanged={vi.fn()} />)
    expect(screen.queryByRole('button', { name: 'Cancelar item' })).not.toBeInTheDocument()
  })

  it('asks for confirmation before cancelling', async () => {
    cancelOrderItem.mockResolvedValue(undefined)
    const onChanged = vi.fn()
    render(<BuyerCancelActions itemId="item-1" status="placed" onChanged={onChanged} />)
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: 'Cancelar item' }))
    expect(cancelOrderItem).not.toHaveBeenCalled()

    await user.click(screen.getByRole('button', { name: 'Confirmar cancelamento' }))
    expect(cancelOrderItem).toHaveBeenCalledWith('item-1')
    expect(onChanged).toHaveBeenCalledOnce()
  })
})
