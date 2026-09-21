import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { OpsConversation, OpsOrderItemDetail } from '../../types/ops'
import { OpsOrderItemDetailPage } from './OpsOrderItemDetailPage'

const { fetchOpsOrderItem, fetchOpsItemConversations } = vi.hoisted(() => ({
  fetchOpsOrderItem: vi.fn(),
  fetchOpsItemConversations: vi.fn(),
}))

vi.mock('./api', () => ({ fetchOpsOrderItem, fetchOpsItemConversations }))
vi.mock('../support/InternalCommentsPanel', () => ({
  InternalCommentsPanel: () => <div>Internal comments</div>,
}))

const item: OpsOrderItemDetail = {
  id: 'item-1',
  number: '1042-1',
  offer_id: 'offer-1',
  quantity: 1,
  purchase_price: '199.90',
  status: 'preparing',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  product: { id: 'product-1', name: 'Tenis Runner', description: null },
  buyer: { id: 'buyer-1', name: 'Buyer Demo' },
  seller: { id: 'seller-1', name: 'Loja A' },
  order: { id: 'order-1', number: 1042, created_at: '2026-01-01T00:00:00Z' },
}

const conversation: OpsConversation = {
  id: 'conv-1',
  order_item_id: 'item-1',
  reason: 'atraso',
  status: 'open',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  last_interaction_at: '2026-01-01T00:00:00Z',
  calculated_priority: 'high',
  ops_override: null,
  effective_priority: 'high',
}

describe('OpsOrderItemDetailPage', () => {
  afterEach(() => {
    fetchOpsOrderItem.mockReset()
    fetchOpsItemConversations.mockReset()
  })

  it('lists the item conversations without rendering messages', async () => {
    fetchOpsOrderItem.mockResolvedValue(item)
    fetchOpsItemConversations.mockResolvedValue([conversation])

    render(
      <MemoryRouter initialEntries={['/ops/order-items/item-1']}>
        <Routes>
          <Route path="/ops/order-items/:itemId" element={<OpsOrderItemDetailPage />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(await screen.findByText('Atraso')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Atraso/ })).toHaveAttribute(
      'href',
      '/ops/conversations/conv-1',
    )
    expect(
      screen.getByText('Conteúdo da conversa com o Buyer não é visível para Ops.'),
    ).toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  })
})
