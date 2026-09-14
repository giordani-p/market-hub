import { useParams } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { formatCurrencyBRL, formatDate } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import { fetchSellerOrderItem } from './api'

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
    <div className="page">
      <h1>{item.product.name}</h1>
      {item.product.description && <p className="text-muted">{item.product.description}</p>}

      <Card>
        <dl className="detail-list">
          <dt>Status</dt>
          <dd>
            <StatusBadge status={item.status} />
          </dd>

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

      <p className="text-muted">
        Atualização de status, cancelamento e comunicação com o Buyer chegam na próxima fase.
      </p>
    </div>
  )
}
