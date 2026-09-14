import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { OpsConversationQueueResponse } from '../../types/ops'
import { OpsQueuePage } from './OpsQueuePage'

const { fetchOpsConversationQueue } = vi.hoisted(() => ({
  fetchOpsConversationQueue: vi.fn(),
}))

vi.mock('./api', () => ({ fetchOpsConversationQueue }))

function response(
  overrides: Partial<OpsConversationQueueResponse> = {},
): OpsConversationQueueResponse {
  return {
    items: [
      {
        id: 'conversation-1',
        order_item_id: 'item-1',
        reason: 'atraso',
        status: 'open',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        last_interaction_at: '2026-01-01T00:00:00Z',
        calculated_priority: 'high',
        ops_override: null,
        effective_priority: 'high',
        seller: { id: 'seller-1', name: 'Loja A' },
        product: { id: 'product-1', name: 'Tenis Runner' },
        buyer: { id: 'buyer-1', name: 'Buyer Demo' },
        order_item_status: 'preparing',
        purchase_price: '199.90',
      },
    ],
    page: 1,
    page_size: 20,
    total: 1,
    ...overrides,
  }
}

describe('OpsQueuePage', () => {
  afterEach(() => {
    fetchOpsConversationQueue.mockReset()
  })

  it('renders the conversations returned by the API', async () => {
    fetchOpsConversationQueue.mockResolvedValue(response())
    const { container } = render(
      <MemoryRouter>
        <OpsQueuePage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Tenis Runner')).toBeInTheDocument()
    expect(screen.getByText('Loja A')).toBeInTheDocument()
    expect(container.querySelector('.priority-high')).toHaveTextContent('Alta')
  })

  it('refetches with the priority filter when it changes', async () => {
    fetchOpsConversationQueue.mockResolvedValue(response())
    render(
      <MemoryRouter>
        <OpsQueuePage />
      </MemoryRouter>,
    )
    await screen.findByText('Tenis Runner')
    const user = userEvent.setup()

    await user.selectOptions(screen.getByLabelText('Prioridade'), 'critical')

    await waitFor(() => {
      expect(fetchOpsConversationQueue).toHaveBeenLastCalledWith(
        expect.objectContaining({ effectivePriority: 'critical', page: 1 }),
      )
    })
  })

  it('shows the empty state when there are no open conversations', async () => {
    fetchOpsConversationQueue.mockResolvedValue(response({ items: [], total: 0 }))
    render(
      <MemoryRouter>
        <OpsQueuePage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Nenhuma conversa em aberto.')).toBeInTheDocument()
  })
})
