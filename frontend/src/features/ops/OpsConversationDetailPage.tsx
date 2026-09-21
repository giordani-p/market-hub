import { Link, useParams } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { PriorityBadge } from '../../components/ui/PriorityBadge'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { DetailList } from '../../components/data/DetailList'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { Page } from '../../components/layout/Page'
import { PageHeader } from '../../components/layout/PageHeader'
import { InternalCommentsPanel } from '../support/InternalCommentsPanel'
import { CONVERSATION_REASON_LABELS } from '../conversations/reasons'
import { formatCurrencyBRL, formatDate } from '../../lib/utils/format'
import { formatOrderItemNumber } from '../../lib/utils/orderNumber'
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
    <Page width="wide">
      <PageHeader
        title={item.product.name}
        subtitle="Conteúdo da conversa com o Buyer não é visível para Ops."
        meta={
          <>
            <StatusBadge status={item.status} />
            <PriorityBadge priority={conversation.effective_priority} />
          </>
        }
        breadcrumbs={[
          { label: 'Fila de atendimento', to: '/ops/queue' },
          { label: reasonLabel ?? conversation.reason },
        ]}
        actions={<Link to={`/ops/order-items/${item.id}`}>Ver item</Link>}
      />

      <Card>
        <DetailList
          entries={[
            { term: 'Vendedor', value: item.seller.name },
            { term: 'Comprador', value: item.buyer.name },
            { term: 'Quantidade', value: item.quantity },
            { term: 'Preço', value: formatCurrencyBRL(item.purchase_price) },
            {
              term: 'Pedido',
              value: `${formatOrderItemNumber(item.number)} — ${formatDate(item.order.created_at)}`,
            },
            { term: 'Motivo da conversa', value: reasonLabel ?? conversation.reason },
            {
              term: 'Situação',
              value: conversation.status === 'open' ? 'Aberta' : 'Encerrada',
            },
          ]}
        />
      </Card>

      <Card>
        <PriorityActions conversation={conversation} onChanged={state.retry} />
      </Card>

      <InternalCommentsPanel itemId={item.id} viewerRole="ops" />
    </Page>
  )
}
