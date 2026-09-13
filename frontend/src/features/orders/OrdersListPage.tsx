import { Link } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { formatDate } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import { fetchOrders } from './api'
import { OrderItemsTable } from './OrderItemsTable'

export function OrdersListPage() {
  const state = useAsync(fetchOrders, [])

  return (
    <div className="page">
      <h1>Meus pedidos</h1>

      {state.status === 'loading' && <Spinner label="Carregando pedidos..." />}
      {state.status === 'error' && <ErrorState message={state.error} onRetry={state.retry} />}
      {state.status === 'success' && state.data.length === 0 && (
        <EmptyState title="Você ainda não fez nenhum pedido." />
      )}

      {state.status === 'success' && state.data.length > 0 && (
        <div className="order-list">
          {state.data.map((order) => (
            <Link key={order.id} to={`/buyer/orders/${order.id}`} className="product-link">
              <Card>
                <div className="order-card-header">
                  <span>Pedido #{order.id.slice(0, 8)}</span>
                  <span className="text-muted">{formatDate(order.created_at)}</span>
                </div>
                <OrderItemsTable items={order.items} />
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
