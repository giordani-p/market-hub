import { ORDER_ITEM_STATUS_LABELS } from '../../features/orders/status'
import type { OrderItemStatus } from '../../types/order'

export function StatusBadge({ status }: { status: OrderItemStatus }) {
  return <span className={`status-badge status-${status}`}>{ORDER_ITEM_STATUS_LABELS[status]}</span>
}
