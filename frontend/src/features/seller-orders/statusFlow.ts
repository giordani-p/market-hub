import type { OrderItemStatus } from '../../types/order'

export const STATUS_SEQUENCE: OrderItemStatus[] = ['placed', 'preparing', 'in_transit', 'delivered']

const FORWARD: Partial<Record<OrderItemStatus, OrderItemStatus>> = {
  placed: 'preparing',
  preparing: 'in_transit',
  in_transit: 'delivered',
}

const CANCELLABLE: readonly OrderItemStatus[] = ['placed', 'preparing', 'in_transit']

export function nextStatus(current: OrderItemStatus): OrderItemStatus | null {
  return FORWARD[current] ?? null
}

export function canCancel(current: OrderItemStatus): boolean {
  return CANCELLABLE.includes(current)
}
