import { Link } from 'react-router-dom'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { formatCurrencyBRL } from '../../lib/utils/format'
import { formatOrderItemNumber } from '../../lib/utils/orderNumber'
import type { BuyerOrderItem } from '../../types/order'
import styles from './OrderItemsTable.module.css'

interface OrderItemsTableProps {
  items: BuyerOrderItem[]
  /** Quando presente, cada item vira link para o detalhe do Order Item do Buyer. */
  orderId?: string
}

export function OrderItemsTable({ items, orderId }: OrderItemsTableProps) {
  return (
    <ul className={styles.items}>
      {items.map((item) => {
        const content = (
          <>
            <span className={styles.number}>{formatOrderItemNumber(item.number)}</span>
            <span className={styles.name}>{item.product.name}</span>
            <span className={styles.seller}>{item.seller.name}</span>
            <span className={styles.quantity}>x{item.quantity}</span>
            <span className={styles.price}>{formatCurrencyBRL(item.purchase_price)}</span>
            <StatusBadge status={item.status} />
          </>
        )
        return (
          <li key={item.id} className={styles.item}>
            {orderId ? (
              <Link to={`/buyer/orders/${orderId}/items/${item.id}`} className={styles.link}>
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
