import { Link } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { EmptyState } from '../../components/feedback/EmptyState'
import { Page } from '../../components/layout/Page'
import { PageHeader } from '../../components/layout/PageHeader'
import { Section } from '../../components/layout/Section'
import { formatCurrencyBRL, formatDateTime } from '../../lib/utils/format'
import { formatOrderItemNumber, formatOrderNumber } from '../../lib/utils/orderNumber'
import type { BuyerDashboard } from '../../types/dashboard'
import { SummaryGrid, SummaryStat } from './SummaryStat'
import styles from './BuyerDashboardView.module.css'

export function BuyerDashboardView({ data }: { data: BuyerDashboard }) {
  const { summary, attention, recent } = data

  return (
    <Page>
      <PageHeader title="Início" subtitle="Seus pedidos e o que precisa da sua atenção." />

      <Section title="Resumo">
        <SummaryGrid>
          <SummaryStat label="Pedidos ativos" value={summary.active_orders} to="/buyer/orders" />
          <SummaryStat
            label="Pedidos concluídos"
            value={summary.completed_orders}
            to="/buyer/orders"
          />
        </SummaryGrid>
      </Section>

      <Section title="Atenção">
        {attention.open_conversations === 0 ? (
          <EmptyState title="Nenhuma conversa em aberto." />
        ) : (
          <Link to="/buyer/orders">
            {attention.open_conversations}{' '}
            {attention.open_conversations === 1 ? 'conversa em aberto' : 'conversas em aberto'}
          </Link>
        )}
      </Section>

      <Section
        title="Recentes"
        action={recent.orders.length > 0 ? <Link to="/buyer/orders">Ver todos</Link> : undefined}
      >
        {recent.orders.length === 0 ? (
          <EmptyState
            title="Você ainda não fez nenhum pedido."
            description="Escolha um produto no catálogo para começar."
            action={<Link to="/catalog">Ir ao catálogo</Link>}
          />
        ) : (
          <div className={styles.orderList}>
            {recent.orders.map((order) => (
              <Card key={order.order_id}>
                <div className={styles.orderHeader}>
                  <Link to={`/buyer/orders/${order.order_id}`}>
                    Pedido {formatOrderNumber(order.number)}
                  </Link>
                  <span className={styles.orderMeta}>
                    {formatDateTime(order.created_at)} · {formatCurrencyBRL(order.total_amount)}
                  </span>
                </div>
                <ul className={styles.items}>
                  {order.items.map((item) => (
                    <li key={item.order_item_id} className={styles.item}>
                      <Link
                        to={`/buyer/orders/${order.order_id}/items/${item.order_item_id}`}
                        className={styles.itemLink}
                      >
                        {item.product.name}
                      </Link>
                      <span className={styles.orderMeta}>{formatOrderItemNumber(item.number)}</span>
                      <span className={styles.orderMeta}>{item.seller.name}</span>
                      <span className={styles.orderMeta}>x{item.quantity}</span>
                      <StatusBadge status={item.status} />
                    </li>
                  ))}
                </ul>
              </Card>
            ))}
          </div>
        )}
      </Section>
    </Page>
  )
}
