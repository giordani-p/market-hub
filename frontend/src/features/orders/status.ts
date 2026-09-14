import type { OrderItemStatus } from '../../types/order'

export const ORDER_ITEM_STATUS_LABELS: Record<OrderItemStatus, string> = {
  placed: 'Realizado',
  preparing: 'Em preparação',
  in_transit: 'A caminho',
  delivered: 'Entregue',
  cancelled: 'Cancelado',
}

const BUYER_CANCELLABLE: readonly OrderItemStatus[] = ['placed', 'preparing']

export function canBuyerCancel(status: OrderItemStatus): boolean {
  return BUYER_CANCELLABLE.includes(status)
}
