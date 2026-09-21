import { useParams } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { DetailList } from '../../components/data/DetailList'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { Page } from '../../components/layout/Page'
import { PageHeader } from '../../components/layout/PageHeader'
import { ConversationPanel } from '../conversations/ConversationPanel'
import { formatCurrencyBRL, formatDate } from '../../lib/utils/format'
import { formatOrderItemNumber, formatOrderNumber } from '../../lib/utils/orderNumber'
import { useAsync } from '../../lib/utils/useAsync'
import { fetchOrder } from './api'
import { BuyerCancelActions } from './BuyerCancelActions'

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
    <Page>
      <PageHeader
        title={item.product.name}
        meta={<StatusBadge status={item.status} />}
        breadcrumbs={[
          { label: 'Meus pedidos', to: '/buyer/orders' },
          { label: formatOrderNumber(order.number), to: `/buyer/orders/${order.id}` },
          { label: item.product.name },
        ]}
        actions={
          <BuyerCancelActions itemId={item.id} status={item.status} onChanged={state.retry} />
        }
      />

      <Card>
        <DetailList
          entries={[
            { term: 'Quantidade', value: item.quantity },
            { term: 'Preço', value: formatCurrencyBRL(item.purchase_price) },
            {
              term: 'Pedido',
              value: `${formatOrderItemNumber(item.number)} — ${formatDate(order.created_at)}`,
            },
          ]}
        />
      </Card>

      <ConversationPanel itemId={item.id} itemNumber={item.number} viewerRole="buyer" />
    </Page>
  )
}
