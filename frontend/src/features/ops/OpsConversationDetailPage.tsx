import { Link, useParams } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { PriorityBadge } from '../../components/ui/PriorityBadge'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { InternalCommentsPanel } from '../support/InternalCommentsPanel'
import { CONVERSATION_REASON_LABELS } from '../conversations/reasons'
import { formatCurrencyBRL, formatDate } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import type { ConversationReason } from '../../types/conversation'
import { fetchOpsConversation, fetchOpsOrderItem } from './api'
import { PriorityActions } from './PriorityActions'

export function OpsConversationDetailPage() {
  const { conversationId } = useParams<{ conversationId: string }>()

  const state = useAsync(async () => {
    const conversation = await fetchOpsConversation(conversationId!)
    const item = await fetchOpsOrderItem(conversation.order_item_id)
    return { conversation, item }
  }, [conversationId])

  if (state.status === 'loading') {
    return <Spinner label="Carregando conversa..." />
  }
  if (state.status === 'error') {
    return <ErrorState message={state.error} onRetry={state.retry} />
  }

  const { conversation, item } = state.data
  const reasonLabel = CONVERSATION_REASON_LABELS[conversation.reason as ConversationReason]

  return (
    <div className="page page-wide">
      <div className="item-detail-header">
        <h1>{item.product.name}</h1>
        <StatusBadge status={item.status} />
        <PriorityBadge priority={conversation.effective_priority} />
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

          <dt>Motivo da conversa</dt>
          <dd>{reasonLabel ?? conversation.reason}</dd>

          <dt>Status da conversa</dt>
          <dd>{conversation.status === 'open' ? 'Aberta' : 'Encerrada'}</dd>
        </dl>
      </Card>

      <p className="text-muted">Conteúdo da conversa com o Buyer não é visível para Ops.</p>
      <p>
        <Link to={`/ops/order-items/${item.id}`}>Ver item</Link>
      </p>

      <PriorityActions conversation={conversation} onChanged={state.retry} />

      <InternalCommentsPanel itemId={item.id} viewerRole="ops" />
    </div>
  )
}
