import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Conversation, Message } from '../../types/conversation'
import { ConversationPanel } from './ConversationPanel'

const { fetchItemConversations, openConversation, fetchMessages, sendMessage, closeConversation } =
  vi.hoisted(() => ({
    fetchItemConversations: vi.fn(),
    openConversation: vi.fn(),
    fetchMessages: vi.fn(),
    sendMessage: vi.fn(),
    closeConversation: vi.fn(),
  }))

vi.mock('./api', () => ({
  fetchItemConversations,
  openConversation,
  fetchMessages,
  sendMessage,
  closeConversation,
}))

const openConv: Conversation = {
  id: 'conv-1',
  order_item_id: 'item-1',
  reason: 'suporte',
  status: 'open',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  last_interaction_at: '2026-01-01T00:00:00Z',
  effective_priority: 'medium',
}

function message(overrides: Partial<Message>): Message {
  return {
    id: 'msg-1',
    conversation_id: 'conv-1',
    author_type: 'buyer',
    author_user_id: 'buyer-1',
    content: 'Oi',
    created_at: '2026-01-01T10:00:00Z',
    ...overrides,
  }
}

function renderPanel(viewerRole: 'buyer' | 'seller' = 'seller') {
  return render(<ConversationPanel itemId="item-1" itemNumber="1042-1" viewerRole={viewerRole} />)
}

describe('ConversationPanel', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('offers to start a conversation when none is open', async () => {
    fetchItemConversations.mockResolvedValue([])
    renderPanel()

    expect(await screen.findByText('Nenhuma conversa no pedido #1042-1 ainda.')).toBeInTheDocument()
    expect(screen.getByText('Pedido #1042-1')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Iniciar conversa' })).toBeInTheDocument()
  })

  it('opens a conversation and loads its (empty) thread', async () => {
    fetchItemConversations.mockResolvedValue([])
    openConversation.mockResolvedValue(openConv)
    fetchMessages.mockResolvedValue({ items: [], from: '', to: '', has_older: false })
    renderPanel()
    await screen.findByRole('button', { name: 'Iniciar conversa' })
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: 'Iniciar conversa' }))

    await waitFor(() => expect(openConversation).toHaveBeenCalledWith('item-1', 'suporte'))
    await waitFor(() => expect(fetchMessages).toHaveBeenCalledWith('conv-1', undefined))
  })

  it('renders buyer and seller messages distinctly and sends a new one', async () => {
    fetchItemConversations.mockResolvedValue([openConv])
    fetchMessages.mockResolvedValue({
      items: [message({ id: 'm1', author_type: 'buyer', content: 'Oi' })],
      from: '',
      to: '',
      has_older: false,
    })
    sendMessage.mockResolvedValue(
      message({ id: 'm2', author_type: 'seller', content: 'Olá, tudo bem?' }),
    )
    renderPanel()

    const buyerBubble = (await screen.findByText('Oi')).closest('[data-author]')
    expect(buyerBubble).toHaveAttribute('data-author', 'theirs')

    const user = userEvent.setup()
    await user.type(
      screen.getByPlaceholderText('Escrever sobre o pedido #1042-1…'),
      'Olá, tudo bem?',
    )
    await user.click(screen.getByRole('button', { name: 'Enviar' }))

    expect(sendMessage).toHaveBeenCalledWith('conv-1', 'Olá, tudo bem?')
    const sellerBubble = (await screen.findByText('Olá, tudo bem?')).closest('[data-author]')
    expect(sellerBubble).toHaveAttribute('data-author', 'mine')
  })

  it('disables the composer once the conversation is closed', async () => {
    fetchItemConversations.mockResolvedValue([{ ...openConv, status: 'closed' }])
    fetchMessages.mockResolvedValue({ items: [], from: '', to: '', has_older: false })
    renderPanel()

    expect(await screen.findByText('Esta conversa está encerrada.')).toBeInTheDocument()
    expect(
      screen.queryByPlaceholderText('Escrever sobre o pedido #1042-1…'),
    ).not.toBeInTheDocument()
  })

  it("shows the open conversation's priority", async () => {
    fetchItemConversations.mockResolvedValue([openConv])
    fetchMessages.mockResolvedValue({ items: [], from: '', to: '', has_older: false })
    renderPanel()

    expect(await screen.findByText('Média')).toBeInTheDocument()
    expect(screen.getByText('Pedido #1042-1')).toBeInTheDocument()
  })

  it('flips which side is "mine" when the viewer is the buyer', async () => {
    fetchItemConversations.mockResolvedValue([openConv])
    fetchMessages.mockResolvedValue({
      items: [message({ id: 'm1', author_type: 'buyer', content: 'Oi' })],
      from: '',
      to: '',
      has_older: false,
    })
    renderPanel('buyer')

    const bubble = (await screen.findByText('Oi')).closest('[data-author]')
    expect(bubble).toHaveAttribute('data-author', 'mine')
    expect(screen.getByRole('heading', { name: 'Conversa com o vendedor' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Encerrar conversa' })).not.toBeInTheDocument()
  })
})
