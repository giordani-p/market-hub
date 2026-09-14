import { useParams } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { ConversationPanel } from '../conversations/ConversationPanel'
import { InternalCommentsPanel } from '../support/InternalCommentsPanel'
import { formatCurrencyBRL, formatDate } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import { fetchSellerOrderItem } from './api'
import { StatusActions } from './StatusActions'

export function SellerOrderItemDetailPage() {
  const { itemId } = useParams<{ itemId: string }>()
  const state = useAsync(() => fetchSellerOrderItem(itemId!), [itemId])

  if (state.status === 'loading') {
    return <Spinner label="Carregando item..." />
  }
  if (state.status === 'error') {
    return <ErrorState message={state.error} onRetry={state.retry} />
  }

  const item = state.data

  return (
    <div className="page page-wide">
      <h1>{item.product.name}</h1>
      {item.product.description && <p className="text-muted">{item.product.description}</p>}

      <StatusActions itemId={item.id} status={item.status} onChanged={state.retry} />

      <Card>
        <dl className="detail-list">
          <dt>Buyer</dt>
          <dd>{item.buyer.name}</dd>

          <dt>Quantidade</dt>
          <dd>{item.quantity}</dd>

          <dt>Preço</dt>
          <dd>{formatCurrencyBRL(item.purchase_price)}</dd>

          <dt>Pedido</dt>
          <dd>
            #{item.order.id.slice(0, 8)} — {formatDate(item.order.created_at)}
          </dd>

          <dt>Criado em</dt>
          <dd>{formatDate(item.created_at)}</dd>
        </dl>
      </Card>

      <div className="detail-columns">
        <ConversationPanel itemId={item.id} viewerRole="seller" />
        <InternalCommentsPanel itemId={item.id} />
      </div>
    </div>
  )
}
