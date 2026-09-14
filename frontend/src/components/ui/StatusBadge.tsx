import { CheckCircle, XCircle } from 'lucide-react'
import { ORDER_ITEM_STATUS_LABELS } from '../../features/orders/status'
import type { OrderItemStatus } from '../../types/order'

/** Estado positivo/negativo tambem ganha icone -- nunca so cor (skill secao 11). */
const STATUS_ICON: Partial<Record<OrderItemStatus, typeof CheckCircle>> = {
  delivered: CheckCircle,
  cancelled: XCircle,
}

export function StatusBadge({ status }: { status: OrderItemStatus }) {
  const Icon = STATUS_ICON[status]
  return (
    <span className={`status-badge status-${status}`}>
      {Icon && <Icon size={14} aria-hidden="true" />}
      {ORDER_ITEM_STATUS_LABELS[status]}
    </span>
  )
}
