import { CheckCircle, XCircle } from 'lucide-react'
import { ORDER_ITEM_STATUS_LABELS } from '../../features/orders/status'
import type { OrderItemStatus } from '../../types/order'
import { Tag, type TagTone } from './Tag'

/** Estado positivo/negativo tambem ganha icone -- nunca so cor (skill secao 11). */
const STATUS_ICON: Partial<Record<OrderItemStatus, typeof CheckCircle>> = {
  delivered: CheckCircle,
  cancelled: XCircle,
}

const STATUS_TONE: Record<OrderItemStatus, TagTone> = {
  placed: 'neutral',
  preparing: 'neutral',
  in_transit: 'neutral',
  delivered: 'success',
  cancelled: 'danger',
}

export function StatusBadge({ status }: { status: OrderItemStatus }) {
  const Icon = STATUS_ICON[status]
  return (
    <Tag tone={STATUS_TONE[status]} dot={!Icon}>
      {Icon && <Icon size={14} aria-hidden="true" />}
      {ORDER_ITEM_STATUS_LABELS[status]}
    </Tag>
  )
}
