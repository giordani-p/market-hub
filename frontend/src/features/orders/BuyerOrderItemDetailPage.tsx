import { useParams } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { ConversationPanel } from '../conversations/ConversationPanel'
import { formatCurrencyBRL, formatDate } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import { fetchOrder } from './api'

export function BuyerOrderItemDetailPage() {
  const { orderId, itemId } = useParams<{ orderId: string; itemId: string }>()
  const state = useAsync(() => fetchOrder(orderId!), [orderId])

  if (state.status === 'loading') {
    return <Spinner label="Carregando pedido..." />
  }
  if (state.status === 'error') {
    return <ErrorState message={state.error} onRetry={state.retry} />
  }

  const order = state.data
  const item = order.items.find((candidate) => candidate.id === itemId)

  if (!item) {
    return <ErrorState message="Item não encontrado neste pedido." />
  }

  return (
    <div className="page page-wide">
      <div className="item-detail-header">
        <h1>{item.product.name}</h1>
        <StatusBadge status={item.status} />
      </div>

      <Card>
        <dl className="detail-list">
          <dt>Quantidade</dt>
          <dd>{item.quantity}</dd>

          <dt>Preço</dt>
          <dd>{formatCurrencyBRL(item.purchase_price)}</dd>

          <dt>Pedido</dt>
          <dd>
            #{order.id.slice(0, 8)} — {formatDate(order.created_at)}
          </dd>
        </dl>
      </Card>

      <ConversationPanel itemId={item.id} viewerRole="buyer" />
    </div>
  )
}
