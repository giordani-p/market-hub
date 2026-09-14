import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { InternalComment } from '../../types/support'
import { InternalCommentsPanel } from './InternalCommentsPanel'

const { fetchInternalComments, createInternalComment } = vi.hoisted(() => ({
  fetchInternalComments: vi.fn(),
  createInternalComment: vi.fn(),
}))

vi.mock('./api', () => ({ fetchInternalComments, createInternalComment }))

const comment: InternalComment = {
  id: 'comment-1',
  order_item_id: 'item-1',
  author_id: 'ops-1',
  author_type: 'ops',
  content: 'Cliente pediu prioridade.',
  created_at: '2026-01-01T12:00:00Z',
}

describe('InternalCommentsPanel', () => {
  afterEach(() => {
    fetchInternalComments.mockReset()
    createInternalComment.mockReset()
  })

  it('shows the empty state with no comments', async () => {
    fetchInternalComments.mockResolvedValue([])
    render(<InternalCommentsPanel itemId="item-1" />)

    expect(await screen.findByText('Nenhum comentário interno ainda.')).toBeInTheDocument()
  })

  it('lists existing comments with their author, defaulting to viewerRole seller', async () => {
    fetchInternalComments.mockResolvedValue([comment])
    render(<InternalCommentsPanel itemId="item-1" />)

    expect(await screen.findByText('Cliente pediu prioridade.')).toBeInTheDocument()
    expect(screen.getByText('Ops')).toBeInTheDocument()
    expect(fetchInternalComments).toHaveBeenCalledWith('item-1', 'seller')
  })

  it('creates a new comment and refreshes the list', async () => {
    fetchInternalComments.mockResolvedValueOnce([]).mockResolvedValueOnce([comment])
    createInternalComment.mockResolvedValue(comment)
    render(<InternalCommentsPanel itemId="item-1" />)
    await screen.findByText('Nenhum comentário interno ainda.')
    const user = userEvent.setup()

    await user.type(
      screen.getByPlaceholderText('Registrar comentário interno...'),
      'Cliente pediu prioridade.',
    )
    await user.click(screen.getByRole('button', { name: 'Registrar' }))

    expect(createInternalComment).toHaveBeenCalledWith('item-1', 'Cliente pediu prioridade.', 'seller')
    expect(await screen.findByText('Cliente pediu prioridade.')).toBeInTheDocument()
  })

  it('labels the seller as the other author when viewed as ops', async () => {
    fetchInternalComments.mockResolvedValue([{ ...comment, author_type: 'seller' }])
    render(<InternalCommentsPanel itemId="item-1" viewerRole="ops" />)

    expect(await screen.findByText('Cliente pediu prioridade.')).toBeInTheDocument()
    expect(screen.getByText('Seller')).toBeInTheDocument()
    expect(fetchInternalComments).toHaveBeenCalledWith('item-1', 'ops')
  })

  it('labels its own comment as "Você" when viewed as ops', async () => {
    fetchInternalComments.mockResolvedValue([comment])
    render(<InternalCommentsPanel itemId="item-1" viewerRole="ops" />)

    expect(await screen.findByText('Cliente pediu prioridade.')).toBeInTheDocument()
    expect(screen.getByText('Você')).toBeInTheDocument()
  })

  it('creates a comment through the ops route when viewerRole is ops', async () => {
    fetchInternalComments.mockResolvedValueOnce([]).mockResolvedValueOnce([comment])
    createInternalComment.mockResolvedValue(comment)
    render(<InternalCommentsPanel itemId="item-1" viewerRole="ops" />)
    await screen.findByText('Nenhum comentário interno ainda.')
    const user = userEvent.setup()

    await user.type(
      screen.getByPlaceholderText('Registrar comentário interno...'),
      'Retorno da Ops.',
    )
    await user.click(screen.getByRole('button', { name: 'Registrar' }))

    expect(createInternalComment).toHaveBeenCalledWith('item-1', 'Retorno da Ops.', 'ops')
  })
})
