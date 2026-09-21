import { apiRequest } from '../../lib/api/client'
import type {
  OpsConversation,
  OpsConversationQueueFilters,
  OpsConversationQueueResponse,
  OpsOrderItemDetail,
  OpsOrderItemFilters,
  OpsOrderItemListResponse,
} from '../../types/ops'

export function buildOpsConversationQueueQuery(filters: OpsConversationQueueFilters): string {
  const params = new URLSearchParams()
  if (filters.page !== undefined) {
    params.set('page', String(filters.page))
  }
  if (filters.pageSize !== undefined) {
    params.set('page_size', String(filters.pageSize))
  }
  if (filters.sellerId) {
    params.set('seller_id', filters.sellerId)
  }
  if (filters.orderItemId) {
    params.set('order_item_id', filters.orderItemId)
  }
  if (filters.number) {
    params.set('number', filters.number)
  }
  if (filters.effectivePriority) {
    params.set('effective_priority', filters.effectivePriority)
  }
  const query = params.toString()
  return query ? `?${query}` : ''
}

export function fetchOpsConversationQueue(
  filters: OpsConversationQueueFilters,
): Promise<OpsConversationQueueResponse> {
  return apiRequest<OpsConversationQueueResponse>(
    `/ops/conversations${buildOpsConversationQueueQuery(filters)}`,
  )
}

export function fetchOpsConversation(conversationId: string): Promise<OpsConversation> {
  return apiRequest<OpsConversation>(`/ops/conversations/${conversationId}`)
}

export function fetchOpsOrderItem(orderItemId: string): Promise<OpsOrderItemDetail> {
  return apiRequest<OpsOrderItemDetail>(`/ops/order-items/${orderItemId}`)
}

export function refreshOpsPriority(conversationId: string): Promise<OpsConversation> {
  return apiRequest<OpsConversation>(`/ops/conversations/${conversationId}/priority/refresh`, {
    method: 'POST',
  })
}

export function applyOpsCritical(
  conversationId: string,
  justification: string,
): Promise<OpsConversation> {
  return apiRequest<OpsConversation>(`/ops/conversations/${conversationId}/critical`, {
    method: 'POST',
    body: { justification },
  })
}

export function removeOpsCritical(conversationId: string): Promise<OpsConversation> {
  return apiRequest<OpsConversation>(`/ops/conversations/${conversationId}/critical/remove`, {
    method: 'POST',
  })
}

export function buildOpsOrderItemsQuery(filters: OpsOrderItemFilters): string {
  const params = new URLSearchParams()
  if (filters.page !== undefined) {
    params.set('page', String(filters.page))
  }
  if (filters.pageSize !== undefined) {
    params.set('page_size', String(filters.pageSize))
  }
  if (filters.status) {
    params.set('status', filters.status)
  }
  if (filters.from) {
    params.set('from', filters.from)
  }
  if (filters.to) {
    params.set('to', filters.to)
  }
  if (filters.orderItemId) {
    params.set('order_item_id', filters.orderItemId)
  }
  if (filters.number) {
    params.set('number', filters.number)
  }
  if (filters.sellerId) {
    params.set('seller_id', filters.sellerId)
  }
  const query = params.toString()
  return query ? `?${query}` : ''
}

export function fetchOpsOrderItems(
  filters: OpsOrderItemFilters,
): Promise<OpsOrderItemListResponse> {
  return apiRequest<OpsOrderItemListResponse>(`/ops/order-items${buildOpsOrderItemsQuery(filters)}`)
}

export function fetchOpsItemConversations(itemId: string): Promise<OpsConversation[]> {
  return apiRequest<OpsConversation[]>(`/ops/order-items/${itemId}/conversations`)
}
