import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { Offer } from '../../types/catalog'
import { PurchasePanel } from './PurchasePanel'

const { createOrder } = vi.hoisted(() => ({ createOrder: vi.fn() }))

vi.mock('../orders/api', () => ({ createOrder }))

const offer: Offer = {
  id: 'offer-1',
  product_id: 'product-1',
  seller_id: 'seller-1',
  price: '299.00',
  stock: 2,
  available: true,
}

describe('PurchasePanel', () => {
  it('caps the quantity at the offer stock', async () => {
    render(<PurchasePanel offers={[offer]} onPurchased={vi.fn()} />)
    const user = userEvent.setup()

    const quantityInput = screen.getByLabelText('Quantidade') as HTMLInputElement
    await user.clear(quantityInput)
    await user.type(quantityInput, '5')

    expect(quantityInput.value).toBe('2')
  })

  it('buys with the selected offer and calls onPurchased on success', async () => {
    const order = { id: 'order-1', buyer_id: 'buyer-1', items: [], created_at: '', updated_at: '' }
    createOrder.mockResolvedValueOnce(order)
    const onPurchased = vi.fn()
    render(<PurchasePanel offers={[offer]} onPurchased={onPurchased} />)
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: 'Comprar' }))

    expect(createOrder).toHaveBeenCalledWith({
      items: [{ offer_id: 'offer-1', quantity: 1, expected_price: '299.00' }],
    })
    expect(onPurchased).toHaveBeenCalledWith(order)
  })

  it('shows the rejection reason without navigating away', async () => {
    const { ApiRequestError } = await import('../../lib/api/client')
    createOrder.mockRejectedValueOnce(
      new ApiRequestError({
        status: 409,
        code: 'checkout_rejected',
        message: 'One or more items require review',
        details: {
          code: 'checkout_rejected',
          message: 'One or more items require review',
          items: [{ offer_id: 'offer-1', reason: 'insufficient_stock' }],
        },
      }),
    )
    const onPurchased = vi.fn()
    render(<PurchasePanel offers={[offer]} onPurchased={onPurchased} />)
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: 'Comprar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Estoque insuficiente para a quantidade escolhida.',
    )
    expect(onPurchased).not.toHaveBeenCalled()
  })
})
