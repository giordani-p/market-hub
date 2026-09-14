import { Link } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { EmptyState } from '../../components/feedback/EmptyState'
import { formatCurrencyBRL, formatDateTime } from '../../lib/utils/format'
import type { BuyerDashboard } from '../../types/dashboard'
import { SummaryStat } from './SummaryStat'

export function BuyerDashboardView({ data }: { data: BuyerDashboard }) {
  const { summary, attention, recent } = data

  return (
    <div className="page page-wide">
      <h1>Início</h1>

      <section className="dashboard-section">
        <h2>Resumo</h2>
        <div className="dashboard-summary">
          <SummaryStat label="Pedidos ativos" value={summary.active_orders} to="/buyer/orders" />
          <SummaryStat
            label="Pedidos concluídos"
            value={summary.completed_orders}
            to="/buyer/orders"
          />
        </div>
      </section>

      <section className="dashboard-section">
        <h2>Atenção</h2>
        {attention.open_conversations === 0 ? (
          <EmptyState title="Nenhuma conversa em aberto." />
        ) : (
          <Link to="/buyer/orders" className="dashboard-attention-link">
            {attention.open_conversations}{' '}
            {attention.open_conversations === 1 ? 'conversa em aberto' : 'conversas em aberto'}
          </Link>
        )}
      </section>

      <section className="dashboard-section">
        <h2>Recentes</h2>
        {recent.orders.length === 0 ? (
          <>
            <EmptyState title="Você ainda não fez nenhum pedido." />
            <Link to="/catalog">Ir ao catálogo</Link>
          </>
        ) : (
          <div className="order-list">
            {recent.orders.map((order) => (
              <Card key={order.order_id}>
                <div className="order-card-header">
                  <Link to={`/buyer/orders/${order.order_id}`}>
                    Pedido #{order.order_id.slice(0, 8)}
                  </Link>
                </div>
                <p className="text-muted">
                  {formatDateTime(order.created_at)} · {formatCurrencyBRL(order.total_amount)}
                </p>
                <ul className="order-items">
                  {order.items.map((item) => (
                    <li key={item.order_item_id} className="order-item-row">
                      <Link
                        to={`/buyer/orders/${order.order_id}/items/${item.order_item_id}`}
                        className="order-item-link"
                      >
                        <span>{item.product.name}</span>
                        <span className="text-muted">x{item.quantity}</span>
                        <StatusBadge status={item.status} />
                      </Link>
                    </li>
                  ))}
                </ul>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
