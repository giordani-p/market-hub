import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { BuyerDashboard, OpsDashboard, SellerDashboard } from '../../types/dashboard'
import { DashboardPage } from './DashboardPage'

const { fetchDashboard } = vi.hoisted(() => ({ fetchDashboard: vi.fn() }))

vi.mock('./api', () => ({ fetchDashboard }))

const emptySeller: SellerDashboard = {
  role: 'seller',
  summary: {
    total_order_items: 0,
    active_order_items: 0,
    order_items_by_status: {
      placed: 0,
      preparing: 0,
      in_transit: 0,
      delivered: 0,
      cancelled: 0,
    },
  },
  attention: { open_conversations: 0 },
  recent: { order_items: [] },
}

const emptyBuyer: BuyerDashboard = {
  role: 'buyer',
  summary: { active_orders: 0, completed_orders: 0 },
  attention: { open_conversations: 0 },
  recent: { orders: [] },
}

const emptyOps: OpsDashboard = {
  role: 'ops',
  summary: {
    open_conversations: 0,
    conversations_by_priority: { critical: 0, high: 0, medium: 0, low: 0 },
  },
  attention: { priority_queue_preview: [] },
  recent: {},
}

describe('DashboardPage', () => {
  afterEach(() => {
    fetchDashboard.mockReset()
  })

  it('shows the seller empty states without hiding the page', async () => {
    fetchDashboard.mockResolvedValue(emptySeller)
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'Início' })).toBeInTheDocument()
    expect(screen.getByText('Nenhuma conversa em aberto.')).toBeInTheDocument()
    expect(screen.getByText('Nenhum pedido na sua operação.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Ir ao catálogo' })).toHaveAttribute('href', '/catalog')
  })

  it('shows the buyer empty states and does not render a queue preview', async () => {
    fetchDashboard.mockResolvedValue(emptyBuyer)
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Você ainda não fez nenhum pedido.')).toBeInTheDocument()
    expect(screen.queryByText('Ver fila completa')).not.toBeInTheDocument()
    expect(screen.queryByText('Crítica')).not.toBeInTheDocument()
  })

  it('shows item status on buyer recents, not the derived order status', async () => {
    fetchDashboard.mockResolvedValue({
      ...emptyBuyer,
      summary: { active_orders: 1, completed_orders: 0 },
      recent: {
        orders: [
          {
            order_id: 'order-1',
            number: 1042,
            created_at: '2026-01-01T00:00:00Z',
            status: 'in_progress',
            total_amount: '199.90',
            items: [
              {
                order_item_id: 'item-1',
                number: '1042-1',
                product: { id: 'product-1', name: 'Tenis Runner' },
                seller: { id: 'seller-1', name: 'Loja A' },
                quantity: 1,
                status: 'preparing',
              },
            ],
          },
        ],
      },
    } satisfies BuyerDashboard)

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Tenis Runner')).toBeInTheDocument()
    expect(screen.getByText('Loja A')).toBeInTheDocument()
    expect(screen.getByText('Em preparação')).toBeInTheDocument()
    expect(screen.queryByText('Em andamento')).not.toBeInTheDocument()
  })

  it('links ops preview items to the conversation detail', async () => {
    fetchDashboard.mockResolvedValue({
      ...emptyOps,
      summary: {
        open_conversations: 1,
        conversations_by_priority: { critical: 1, high: 0, medium: 0, low: 0 },
      },
      attention: {
        priority_queue_preview: [
          {
            conversation_id: 'conv-1',
            order_item_id: 'item-1',
            number: '1042-1',
            effective_priority: 'critical',
            calculated_priority: 'high',
            ops_override: 'critical',
            reason: 'atraso',
            last_interaction_at: '2026-01-01T00:00:00Z',
            seller: { id: 'seller-1', name: 'Loja A' },
            buyer: { id: 'buyer-1', name: 'Buyer Demo' },
            product: { id: 'product-1', name: 'Tenis Runner' },
            order_item_status: 'preparing',
            purchase_price: '199.90',
          },
        ],
      },
    } satisfies OpsDashboard)

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Tenis Runner')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Tenis Runner/ })).toHaveAttribute(
      'href',
      '/ops/conversations/conv-1',
    )
    expect(screen.getByRole('link', { name: 'Ver fila completa' })).toHaveAttribute(
      'href',
      '/ops/queue',
    )
  })
})
