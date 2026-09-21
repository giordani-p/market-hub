import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { BuyerOrderItem } from '../../types/order'
import { OrderItemsTable } from './OrderItemsTable'

const item: BuyerOrderItem = {
  id: 'item-1',
  number: '1042-1',
  order_id: 'order-1',
  offer_id: 'offer-1',
  quantity: 3,
  purchase_price: '150.00',
  status: 'delivered',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  product: { id: 'product-1', name: 'Tenis XYZ' },
}

describe('OrderItemsTable', () => {
  it('renders product, quantity, price and status label', () => {
    render(<OrderItemsTable items={[item]} />)

    expect(screen.getByText('Tenis XYZ')).toBeInTheDocument()
    expect(screen.getByText('#1042-1')).toBeInTheDocument()
    expect(screen.getByText('x3')).toBeInTheDocument()
    expect(screen.getByText('R$ 150,00')).toBeInTheDocument()
    expect(screen.getByText('Entregue')).toBeInTheDocument()
  })
})
