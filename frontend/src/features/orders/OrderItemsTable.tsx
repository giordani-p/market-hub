import { Link } from 'react-router-dom'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { formatCurrencyBRL } from '../../lib/utils/format'
import type { BuyerOrderItem } from '../../types/order'

interface OrderItemsTableProps {
  items: BuyerOrderItem[]
  /** Quando presente, cada item vira link para o detalhe do Order Item do Buyer. */
  orderId?: string
}

export function OrderItemsTable({ items, orderId }: OrderItemsTableProps) {
  return (
    <ul className="order-items">
      {items.map((item) => {
        const content = (
          <>
            <span>{item.product.name}</span>
            <span className="text-muted">x{item.quantity}</span>
            <span>{formatCurrencyBRL(item.purchase_price)}</span>
            <StatusBadge status={item.status} />
          </>
        )
        return (
          <li key={item.id} className="order-item-row">
            {orderId ? (
              <Link to={`/buyer/orders/${orderId}/items/${item.id}`} className="order-item-link">
                {content}
              </Link>
            ) : (
              content
            )}
          </li>
        )
      })}
    </ul>
  )
}
