import { Link } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { EmptyState } from '../../components/feedback/EmptyState'
import { formatCurrencyBRL, formatDateTime } from '../../lib/utils/format'
import type { SellerDashboard } from '../../types/dashboard'
import type { OrderItemStatus } from '../../types/order'
import { ORDER_ITEM_STATUS_LABELS } from '../orders/status'
import { SummaryStat } from './SummaryStat'

const STATUS_KEYS: OrderItemStatus[] = [
  'placed',
  'preparing',
  'in_transit',
  'delivered',
  'cancelled',
]

export function SellerDashboardView({ data }: { data: SellerDashboard }) {
  const { summary, attention, recent } = data

  return (
    <div className="page page-wide">
      <h1>Início</h1>

      <section className="dashboard-section">
        <h2>Resumo</h2>
        <div className="dashboard-summary">
          <SummaryStat label="Total" value={summary.total_order_items} to="/seller/orders" />
          <SummaryStat label="Ativos" value={summary.active_order_items} to="/seller/orders" />
          {STATUS_KEYS.map((status) => (
            <SummaryStat
              key={status}
              label={ORDER_ITEM_STATUS_LABELS[status]}
              value={summary.order_items_by_status[status]}
              to={`/seller/orders?status=${status}`}
            />
          ))}
        </div>
      </section>

      <section className="dashboard-section">
        <h2>Atenção</h2>
        {attention.open_conversations === 0 ? (
          <EmptyState title="Nenhuma conversa em aberto." />
        ) : (
          <Link to="/seller/orders" className="dashboard-attention-link">
            {attention.open_conversations}{' '}
            {attention.open_conversations === 1 ? 'conversa em aberto' : 'conversas em aberto'}
          </Link>
        )}
      </section>

      <section className="dashboard-section">
        <h2>Recentes</h2>
        {recent.order_items.length === 0 ? (
          <>
            <EmptyState title="Nenhum pedido na sua operação." />
            <Link to="/catalog">Ir ao catálogo</Link>
          </>
        ) : (
          <div className="order-list">
            {recent.order_items.map((item) => (
              <Link
                key={item.order_item_id}
                to={`/seller/orders/${item.order_item_id}`}
                className="product-link"
              >
                <Card>
                  <div className="order-item-row">
                    <span>{item.product.name}</span>
                    <span className="text-muted">{item.buyer.name}</span>
                    <span className="text-muted">x{item.quantity}</span>
                    <span>{formatCurrencyBRL(item.purchase_price)}</span>
                    <StatusBadge status={item.status} />
                  </div>
                  <span className="text-muted">{formatDateTime(item.created_at)}</span>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
