import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Order } from '../../types/order'
import { OrdersListPage } from './OrdersListPage'

const { fetchOrders } = vi.hoisted(() => ({ fetchOrders: vi.fn() }))

vi.mock('./api', () => ({ fetchOrders }))

function order(overrides: Partial<Order> = {}): Order {
  return {
    id: 'order-1',
    number: 1042,
    buyer_id: 'buyer-1',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    items: [
      {
        id: 'item-1',
        number: '1042-1',
        order_id: 'order-1',
        offer_id: 'offer-1',
        quantity: 1,
        purchase_price: '10.00',
        status: 'placed',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        product: { id: 'product-1', name: 'Tenis Runner' },
        seller: { id: 'seller-1', name: 'Loja A' },
      },
    ],
    ...overrides,
  }
}

describe('OrdersListPage', () => {
  afterEach(() => {
    fetchOrders.mockReset()
  })

  it('renders the public order number and the pedido field', async () => {
    fetchOrders.mockResolvedValue([order()])
    render(
      <MemoryRouter>
        <OrdersListPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Pedido #1042')).toBeInTheDocument()
    expect(screen.getByLabelText('Pedido')).toBeInTheDocument()
    expect(screen.getByText('Tenis Runner')).toBeInTheDocument()
  })

  it('filters the list from the number query string', async () => {
    fetchOrders.mockResolvedValue([
      order(),
      order({
        id: 'order-2',
        number: 1080,
        items: [
          {
            id: 'item-2',
            number: '1080-1',
            order_id: 'order-2',
            offer_id: 'offer-2',
            quantity: 1,
            purchase_price: '20.00',
            status: 'placed',
            created_at: '2026-01-02T00:00:00Z',
            updated_at: '2026-01-02T00:00:00Z',
            product: { id: 'product-2', name: 'Mochila Trail' },
            seller: { id: 'seller-2', name: 'Tech Hub' },
          },
        ],
      }),
    ])
    render(
      <MemoryRouter initialEntries={['/buyer/orders?number=1042']}>
        <OrdersListPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Tenis Runner')).toBeInTheDocument()
    expect(screen.queryByText('Mochila Trail')).not.toBeInTheDocument()
  })

  it('shows an error for an incomplete number without emptying the list', async () => {
    fetchOrders.mockResolvedValue([order()])
    render(
      <MemoryRouter initialEntries={['/buyer/orders?number=1042-']}>
        <OrdersListPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Tenis Runner')).toBeInTheDocument()
    expect(screen.getByText(/Informe o número do pedido/)).toBeInTheDocument()
    expect(screen.queryByText('Nenhum pedido corresponde à busca.')).not.toBeInTheDocument()
  })
})
