import { apiRequest } from '../../lib/api/client'
import type {
  AppNotification,
  NotificationListResponse,
  UnreadCountResponse,
} from '../../types/notification'

export interface NotificationFilters {
  page?: number
  pageSize?: number
}

export function buildNotificationsQuery(filters: NotificationFilters): string {
  const params = new URLSearchParams()
  if (filters.page !== undefined) {
    params.set('page', String(filters.page))
  }
  if (filters.pageSize !== undefined) {
    params.set('page_size', String(filters.pageSize))
  }
  const query = params.toString()
  return query ? `?${query}` : ''
}

export function fetchNotifications(
  filters: NotificationFilters = {},
): Promise<NotificationListResponse> {
  return apiRequest<NotificationListResponse>(`/notifications${buildNotificationsQuery(filters)}`)
}

export function fetchUnreadCount(): Promise<UnreadCountResponse> {
  return apiRequest<UnreadCountResponse>('/notifications/unread-count')
}

export function markNotificationRead(notificationId: string): Promise<AppNotification> {
  return apiRequest<AppNotification>(`/notifications/${notificationId}/read`, {
    method: 'PATCH',
  })
}

export function markAllNotificationsRead(): Promise<unknown> {
  return apiRequest('/notifications/read-all', { method: 'PATCH' })
}

/**
 * So o minimo pra resolver a rota de deep link (secao 2 da
 * FRONTEND_F5_SPEC) -- nao os tipos completos de `seller-orders` ou
 * `conversations`, que sao de outra feature.
 */
export interface OrderItemRouteContext {
  id: string
  order: { id: string }
}

export function fetchOrderItemRouteContext(itemId: string): Promise<OrderItemRouteContext> {
  return apiRequest<OrderItemRouteContext>(`/order-items/${itemId}`)
}

export interface ConversationRouteContext {
  id: string
  order_item_id: string
}

export function fetchConversationRouteContext(
  conversationId: string,
): Promise<ConversationRouteContext> {
  return apiRequest<ConversationRouteContext>(`/conversations/${conversationId}`)
}
