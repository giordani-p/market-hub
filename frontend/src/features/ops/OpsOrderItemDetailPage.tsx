import { Link, useParams } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { PriorityBadge } from '../../components/ui/PriorityBadge'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { InternalCommentsPanel } from '../support/InternalCommentsPanel'
import { CONVERSATION_REASON_LABELS } from '../conversations/reasons'
import { formatCurrencyBRL, formatDate, formatDateTime } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import type { ConversationReason } from '../../types/conversation'
import { fetchOpsItemConversations, fetchOpsOrderItem } from './api'

export function OpsOrderItemDetailPage() {
  const { itemId } = useParams<{ itemId: string }>()

  const state = useAsync(async () => {
    const [item, conversations] = await Promise.all([
      fetchOpsOrderItem(itemId!),
      fetchOpsItemConversations(itemId!),
    ])
    return { item, conversations }
  }, [itemId])

  if (state.status === 'loading') {
    return <Spinner label="Carregando item..." />
  }
  if (state.status === 'error') {
    return <ErrorState message={state.error} onRetry={state.retry} />
  }

  const { item, conversations } = state.data

  return (
    <div className="page page-wide">
      <div className="item-detail-header">
        <h1>{item.product.name}</h1>
        <StatusBadge status={item.status} />
      </div>
      {item.product.description && <p className="text-muted">{item.product.description}</p>}

      <Card>
        <dl className="detail-list">
          <dt>Seller</dt>
          <dd>{item.seller.name}</dd>

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
        </dl>
      </Card>

      <section className="dashboard-section">
        <h2>Conversas</h2>
        <p className="text-muted">Conteúdo da conversa com o Buyer não é visível para Ops.</p>
        {conversations.length === 0 ? (
          <EmptyState title="Nenhuma conversa neste item." />
        ) : (
          <div className="order-list">
            {conversations.map((conversation) => {
              const reasonLabel =
                CONVERSATION_REASON_LABELS[conversation.reason as ConversationReason]
              return (
                <Link
                  key={conversation.id}
                  to={`/ops/conversations/${conversation.id}`}
                  className="product-link"
                >
                  <Card>
                    <div className="order-item-row">
                      <span>{reasonLabel ?? conversation.reason}</span>
                      <span className="text-muted">
                        {conversation.status === 'open' ? 'Aberta' : 'Encerrada'}
                      </span>
                      <PriorityBadge priority={conversation.effective_priority} />
                    </div>
                    <span className="text-muted">
                      {formatDateTime(conversation.last_interaction_at)}
                    </span>
                  </Card>
                </Link>
              )
            })}
          </div>
        )}
      </section>

      <InternalCommentsPanel itemId={item.id} viewerRole="ops" />
    </div>
  )
}
