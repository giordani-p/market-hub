import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { SellerOrderItemListResponse } from '../../types/order'
import { SellerOrdersListPage } from './SellerOrdersListPage'

const { fetchSellerOrderItems } = vi.hoisted(() => ({ fetchSellerOrderItems: vi.fn() }))

vi.mock('./api', () => ({ fetchSellerOrderItems }))

function response(
  overrides: Partial<SellerOrderItemListResponse> = {},
): SellerOrderItemListResponse {
  return {
    items: [
      {
        order_item_id: 'item-1',
        number: '1042-1',
        product: { id: 'product-1', name: 'Tenis Runner' },
        quantity: 1,
        purchase_price: '199.90',
        status: 'placed',
        created_at: '2026-01-01T00:00:00Z',
        buyer: { id: 'buyer-1', name: 'Buyer Demo' },
        order_id: 'order-1',
      },
    ],
    page: 1,
    page_size: 20,
    total: 1,
    ...overrides,
  }
}

describe('SellerOrdersListPage', () => {
  afterEach(() => {
    fetchSellerOrderItems.mockReset()
  })

  it('renders the items returned by the API', async () => {
    fetchSellerOrderItems.mockResolvedValue(response())
    render(
      <MemoryRouter>
        <SellerOrdersListPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Tenis Runner')).toBeInTheDocument()
    expect(screen.getByText('Buyer Demo')).toBeInTheDocument()
  })

  it('refetches with the status filter when it changes', async () => {
    fetchSellerOrderItems.mockResolvedValue(response())
    render(
      <MemoryRouter>
        <SellerOrdersListPage />
      </MemoryRouter>,
    )
    await screen.findByText('Tenis Runner')
    const user = userEvent.setup()

    await user.selectOptions(screen.getByLabelText('Status'), 'delivered')

    await waitFor(() => {
      expect(fetchSellerOrderItems).toHaveBeenLastCalledWith(
        expect.objectContaining({ status: 'delivered', page: 1 }),
      )
    })
  })

  it('initializes the status filter from the query string', async () => {
    fetchSellerOrderItems.mockResolvedValue(response())
    render(
      <MemoryRouter initialEntries={['/seller/orders?status=delivered']}>
        <SellerOrdersListPage />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(fetchSellerOrderItems).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'delivered', page: 1 }),
      )
    })
  })

  it('shows the empty state when there are no items', async () => {
    fetchSellerOrderItems.mockResolvedValue(response({ items: [], total: 0 }))
    render(
      <MemoryRouter>
        <SellerOrdersListPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Nenhum item encontrado.')).toBeInTheDocument()
  })

  it('sends the public number filter from the query string', async () => {
    fetchSellerOrderItems.mockResolvedValue(response())
    render(
      <MemoryRouter initialEntries={['/seller/orders?number=1042']}>
        <SellerOrdersListPage />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(fetchSellerOrderItems).toHaveBeenCalledWith(
        expect.objectContaining({ number: '1042', page: 1 }),
      )
    })
  })

  it('does not send an incomplete lookup', async () => {
    fetchSellerOrderItems.mockResolvedValue(response())
    render(
      <MemoryRouter initialEntries={['/seller/orders?number=1042-']}>
        <SellerOrdersListPage />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(fetchSellerOrderItems).toHaveBeenCalled()
    })
    expect(fetchSellerOrderItems).toHaveBeenCalledWith(
      expect.not.objectContaining({ number: '1042-' }),
    )
    expect(screen.getByText(/Informe o número do pedido/)).toBeInTheDocument()
  })
})
