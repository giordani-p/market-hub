import { apiRequest } from '../../lib/api/client'
import type { CheckoutRequest, Order } from '../../types/order'

export function fetchOrders(): Promise<Order[]> {
  return apiRequest<Order[]>('/orders')
}

export function fetchOrder(orderId: string): Promise<Order> {
  return apiRequest<Order>(`/orders/${orderId}`)
}

export function createOrder(payload: CheckoutRequest): Promise<Order> {
  return apiRequest<Order>('/orders', { method: 'POST', body: payload })
}

export function cancelOrderItem(itemId: string): Promise<unknown> {
  return apiRequest(`/order-items/${itemId}/cancel`, { method: 'POST' })
}
