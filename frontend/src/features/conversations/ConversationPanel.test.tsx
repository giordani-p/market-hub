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

describe('ConversationPanel', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('offers to start a conversation when none is open', async () => {
    fetchItemConversations.mockResolvedValue([])
    render(<ConversationPanel itemId="item-1" viewerRole="seller" />)

    expect(await screen.findByText('Nenhuma conversa neste pedido ainda.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Iniciar conversa' })).toBeInTheDocument()
  })

  it('opens a conversation and loads its (empty) thread', async () => {
    fetchItemConversations.mockResolvedValue([])
    openConversation.mockResolvedValue(openConv)
    fetchMessages.mockResolvedValue({ items: [], from: '', to: '', has_older: false })
    render(<ConversationPanel itemId="item-1" viewerRole="seller" />)
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
    render(<ConversationPanel itemId="item-1" viewerRole="seller" />)

    const buyerBubble = (await screen.findByText('Oi')).closest('.message-row')
    expect(buyerBubble).toHaveClass('message-row-theirs')

    const user = userEvent.setup()
    await user.type(screen.getByPlaceholderText('Escrever mensagem...'), 'Olá, tudo bem?')
    await user.click(screen.getByRole('button', { name: 'Enviar' }))

    expect(sendMessage).toHaveBeenCalledWith('conv-1', 'Olá, tudo bem?')
    const sellerBubble = (await screen.findByText('Olá, tudo bem?')).closest('.message-row')
    expect(sellerBubble).toHaveClass('message-row-mine')
  })

  it('disables the composer once the conversation is closed', async () => {
    fetchItemConversations.mockResolvedValue([{ ...openConv, status: 'closed' }])
    fetchMessages.mockResolvedValue({ items: [], from: '', to: '', has_older: false })
    render(<ConversationPanel itemId="item-1" viewerRole="seller" />)

    expect(await screen.findByText('Esta conversa está encerrada.')).toBeInTheDocument()
    expect(screen.queryByPlaceholderText('Escrever mensagem...')).not.toBeInTheDocument()
  })

  it("shows the open conversation's priority", async () => {
    fetchItemConversations.mockResolvedValue([openConv])
    fetchMessages.mockResolvedValue({ items: [], from: '', to: '', has_older: false })
    render(<ConversationPanel itemId="item-1" viewerRole="seller" />)

    expect(await screen.findByText('Média')).toBeInTheDocument()
  })

  it('flips which side is "mine" when the viewer is the buyer', async () => {
    fetchItemConversations.mockResolvedValue([openConv])
    fetchMessages.mockResolvedValue({
      items: [message({ id: 'm1', author_type: 'buyer', content: 'Oi' })],
      from: '',
      to: '',
      has_older: false,
    })
    render(<ConversationPanel itemId="item-1" viewerRole="buyer" />)

    const bubble = (await screen.findByText('Oi')).closest('.message-row')
    expect(bubble).toHaveClass('message-row-mine')
    expect(screen.getByRole('heading', { name: 'Conversa com o vendedor' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Encerrar conversa' })).not.toBeInTheDocument()
  })
})
