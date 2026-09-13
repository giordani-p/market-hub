import { formatCurrencyBRL } from '../../lib/utils/format'
import type { BuyerOrderItem } from '../../types/order'
import { ORDER_ITEM_STATUS_LABELS } from './status'

export function OrderItemsTable({ items }: { items: BuyerOrderItem[] }) {
  return (
    <ul className="order-items">
      {items.map((item) => (
        <li key={item.id} className="order-item-row">
          <span>{item.product.name}</span>
          <span className="text-muted">x{item.quantity}</span>
          <span>{formatCurrencyBRL(item.purchase_price)}</span>
          <span className={`status-badge status-${item.status}`}>
            {ORDER_ITEM_STATUS_LABELS[item.status]}
          </span>
        </li>
      ))}
    </ul>
  )
}
