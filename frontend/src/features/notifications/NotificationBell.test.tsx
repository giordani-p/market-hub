import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { AppNotification, NotificationListResponse } from '../../types/notification'
import { NotificationBell } from './NotificationBell'

const {
  fetchUnreadCount,
  fetchNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  fetchOrderItemRouteContext,
  fetchConversationRouteContext,
  navigate,
} = vi.hoisted(() => ({
  fetchUnreadCount: vi.fn(),
  fetchNotifications: vi.fn(),
  markNotificationRead: vi.fn(),
  markAllNotificationsRead: vi.fn(),
  fetchOrderItemRouteContext: vi.fn(),
  fetchConversationRouteContext: vi.fn(),
  navigate: vi.fn(),
}))

vi.mock('./api', () => ({
  fetchUnreadCount,
  fetchNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  fetchOrderItemRouteContext,
  fetchConversationRouteContext,
}))

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>()
  return { ...actual, useNavigate: () => navigate }
})

function notification(overrides: Partial<AppNotification> = {}): AppNotification {
  return {
    id: 'notif-1',
    recipient_id: 'user-1',
    type: 'ORDER_ITEM_STATUS_CHANGED',
    title: 'raw english title (never shown)',
    message: 'raw english message (never shown)',
    entity_type: 'ORDER_ITEM',
    entity_id: 'item-1',
    metadata: { previous_status: 'placed', new_status: 'preparing' },
    created_at: '2026-01-01T00:00:00Z',
    read_at: null,
    ...overrides,
  }
}

function listResponse(overrides: Partial<NotificationListResponse> = {}): NotificationListResponse {
  return {
    items: [notification()],
    page: 1,
    page_size: 10,
    total: 1,
    ...overrides,
  }
}

describe('NotificationBell', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('shows the unread count badge from the API', async () => {
    fetchUnreadCount.mockResolvedValue({ unread_count: 3 })
    render(
      <MemoryRouter>
        <NotificationBell role="seller" />
      </MemoryRouter>,
    )

    expect(await screen.findByText('3')).toBeInTheDocument()
  })

  it('lists notifications with the PT-BR copy, never the raw backend text', async () => {
    fetchUnreadCount.mockResolvedValue({ unread_count: 1 })
    fetchNotifications.mockResolvedValue(listResponse())
    render(
      <MemoryRouter>
        <NotificationBell role="seller" />
      </MemoryRouter>,
    )
    await screen.findByText('1')
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: /notificaç/i }))

    expect(await screen.findByText('Status do pedido atualizado')).toBeInTheDocument()
    expect(screen.getByText('Seu pedido agora está "Em preparação".')).toBeInTheDocument()
    expect(screen.queryByText('raw english title (never shown)')).not.toBeInTheDocument()
  })

  it('shows the empty state when there are no notifications', async () => {
    fetchUnreadCount.mockResolvedValue({ unread_count: 0 })
    fetchNotifications.mockResolvedValue(listResponse({ items: [], total: 0 }))
    render(
      <MemoryRouter>
        <NotificationBell role="seller" />
      </MemoryRouter>,
    )
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: /notificaç/i }))

    expect(await screen.findByText('Nenhuma notificação ainda.')).toBeInTheDocument()
  })

  it('marks all as read and zeroes the badge', async () => {
    fetchUnreadCount.mockResolvedValue({ unread_count: 2 })
    fetchNotifications.mockResolvedValue(listResponse())
    markAllNotificationsRead.mockResolvedValue(undefined)
    render(
      <MemoryRouter>
        <NotificationBell role="seller" />
      </MemoryRouter>,
    )
    await screen.findByText('2')
    const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: /notificaç/i }))
    await screen.findByText('Status do pedido atualizado')

    await user.click(screen.getByRole('button', { name: 'Marcar todas como lidas' }))

    expect(markAllNotificationsRead).toHaveBeenCalledOnce()
    await waitFor(() => expect(screen.queryByText('2')).not.toBeInTheDocument())
  })

  it('marks the notification as read and navigates to the resolved route (seller + ORDER_ITEM)', async () => {
    fetchUnreadCount.mockResolvedValue({ unread_count: 1 })
    fetchNotifications.mockResolvedValue(listResponse())
    markNotificationRead.mockResolvedValue(notification({ read_at: '2026-01-01T01:00:00Z' }))
    render(
      <MemoryRouter>
        <NotificationBell role="seller" />
      </MemoryRouter>,
    )
    await screen.findByText('1')
    const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: /notificaç/i }))
    await screen.findByText('Status do pedido atualizado')

    await user.click(screen.getByText('Status do pedido atualizado'))

    expect(markNotificationRead).toHaveBeenCalledWith('notif-1')
    await waitFor(() => expect(navigate).toHaveBeenCalledWith('/seller/orders/item-1'))
    expect(fetchOrderItemRouteContext).not.toHaveBeenCalled()
    expect(fetchConversationRouteContext).not.toHaveBeenCalled()
  })

  it('resolves the buyer deep link through the order item lookup before navigating', async () => {
    fetchUnreadCount.mockResolvedValue({ unread_count: 1 })
    fetchNotifications.mockResolvedValue(listResponse())
    markNotificationRead.mockResolvedValue(notification({ read_at: '2026-01-01T01:00:00Z' }))
    fetchOrderItemRouteContext.mockResolvedValue({ id: 'item-1', order: { id: 'order-1' } })
    render(
      <MemoryRouter>
        <NotificationBell role="buyer" />
      </MemoryRouter>,
    )
    await screen.findByText('1')
    const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: /notificaç/i }))
    await screen.findByText('Status do pedido atualizado')

    await user.click(screen.getByText('Status do pedido atualizado'))

    expect(fetchOrderItemRouteContext).toHaveBeenCalledWith('item-1')
    await waitFor(() =>
      expect(navigate).toHaveBeenCalledWith('/buyer/orders/order-1/items/item-1'),
    )
  })

  it('closes the dropdown when Escape is pressed', async () => {
    fetchUnreadCount.mockResolvedValue({ unread_count: 1 })
    fetchNotifications.mockResolvedValue(listResponse())
    render(
      <MemoryRouter>
        <NotificationBell role="seller" />
      </MemoryRouter>,
    )
    await screen.findByText('1')
    const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: /notificaç/i }))
    await screen.findByText('Status do pedido atualizado')

    await user.keyboard('{Escape}')

    expect(screen.queryByText('Status do pedido atualizado')).not.toBeInTheDocument()
  })
})
