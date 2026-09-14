import { Link } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { SkeletonList } from '../../components/ui/Skeleton'
import { Page } from '../../components/layout/Page'
import { PageHeader } from '../../components/layout/PageHeader'
import { formatDate } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import { fetchOrders } from './api'
import { OrderItemsTable } from './OrderItemsTable'
import styles from './OrdersListPage.module.css'

export function OrdersListPage() {
  const state = useAsync(fetchOrders, [])

  return (
    <Page>
      <PageHeader title="Meus pedidos" subtitle="Tudo o que você comprou no Market Hub." />

      {state.status === 'loading' && <SkeletonList variant="card" label="Carregando pedidos..." />}
      {state.status === 'error' && <ErrorState message={state.error} onRetry={state.retry} />}
      {state.status === 'success' && state.data.length === 0 && (
        <EmptyState
          title="Você ainda não fez nenhum pedido."
          description="Quando comprar algo, o acompanhamento aparece aqui."
          action={<Link to="/catalog">Ir ao catálogo</Link>}
        />
      )}

      {state.status === 'success' && state.data.length > 0 && (
        <div className={styles.orderList}>
          {state.data.map((order) => (
            <Link key={order.id} to={`/buyer/orders/${order.id}`} className={styles.orderLink}>
              <Card interactive>
                <div className={styles.orderHeader}>
                  <span className={styles.orderId}>Pedido #{order.id.slice(0, 8)}</span>
                  <span className={styles.orderDate}>{formatDate(order.created_at)}</span>
                </div>
                <OrderItemsTable items={order.items} />
              </Card>
            </Link>
          ))}
        </div>
      )}
    </Page>
  )
}
