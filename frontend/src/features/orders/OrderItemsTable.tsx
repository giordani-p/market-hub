import { StatusBadge } from '../../components/ui/StatusBadge'
import { formatCurrencyBRL } from '../../lib/utils/format'
import type { BuyerOrderItem } from '../../types/order'

export function OrderItemsTable({ items }: { items: BuyerOrderItem[] }) {
  return (
    <ul className="order-items">
      {items.map((item) => (
        <li key={item.id} className="order-item-row">
          <span>{item.product.name}</span>
          <span className="text-muted">x{item.quantity}</span>
          <span>{formatCurrencyBRL(item.purchase_price)}</span>
          <StatusBadge status={item.status} />
        </li>
      ))}
    </ul>
  )
}
