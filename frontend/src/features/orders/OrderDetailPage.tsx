import { useParams } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { formatDate } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import { fetchOrder } from './api'
import { OrderItemsTable } from './OrderItemsTable'

export function OrderDetailPage() {
  const { orderId } = useParams<{ orderId: string }>()
  const state = useAsync(() => fetchOrder(orderId!), [orderId])

  if (state.status === 'loading') {
    return <Spinner label="Carregando pedido..." />
  }
  if (state.status === 'error') {
    return <ErrorState message={state.error} onRetry={state.retry} />
  }

  const order = state.data

  return (
    <div className="page">
      <h1>Pedido #{order.id.slice(0, 8)}</h1>
      <p className="text-muted">Criado em {formatDate(order.created_at)}</p>
      <Card>
        <OrderItemsTable items={order.items} orderId={order.id} />
      </Card>
    </div>
  )
}
