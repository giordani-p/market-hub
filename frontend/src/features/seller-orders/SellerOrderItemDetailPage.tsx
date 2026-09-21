import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { Tabs } from '../../components/ui/Tabs'
import { DetailList } from '../../components/data/DetailList'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { Page } from '../../components/layout/Page'
import { PageHeader } from '../../components/layout/PageHeader'
import { ConversationPanel } from '../conversations/ConversationPanel'
import { InternalCommentsPanel } from '../support/InternalCommentsPanel'
import { formatCurrencyBRL, formatDate } from '../../lib/utils/format'
import { formatOrderItemNumber } from '../../lib/utils/orderNumber'
import { useAsync } from '../../lib/utils/useAsync'
import { useMediaQuery } from '../../lib/utils/useMediaQuery'
import { fetchSellerOrderItem } from './api'
import { StatusActions } from './StatusActions'
import styles from './SellerOrderItemDetailPage.module.css'

export function SellerOrderItemDetailPage() {
  const { itemId } = useParams<{ itemId: string }>()
  const state = useAsync(() => fetchSellerOrderItem(itemId!), [itemId])
  const isCompact = useMediaQuery('(max-width: 767px)')
  const [activeTab, setActiveTab] = useState('conversation')

  if (state.status === 'loading') {
    return <Spinner label="Carregando item..." />
  }
  if (state.status === 'error') {
    return <ErrorState message={state.error} onRetry={state.retry} />
  }

  const item = state.data
  const conversation = (
    <ConversationPanel itemId={item.id} itemNumber={item.number} viewerRole="seller" />
  )
  const support = <InternalCommentsPanel itemId={item.id} />

  return (
    <Page width="wide">
      <PageHeader
        title={item.product.name}
        subtitle={item.product.description ?? undefined}
        meta={<StatusBadge status={item.status} />}
        breadcrumbs={[{ label: 'Pedidos', to: '/seller/orders' }, { label: item.product.name }]}
      />

      <Card>
        <StatusActions itemId={item.id} status={item.status} onChanged={state.retry} />
      </Card>

      <Card>
        <DetailList
          entries={[
            { term: 'Comprador', value: item.buyer.name },
            { term: 'Quantidade', value: item.quantity },
            { term: 'Preço', value: formatCurrencyBRL(item.purchase_price) },
            {
              term: 'Pedido',
              value: `${formatOrderItemNumber(item.number)} — ${formatDate(item.order.created_at)}`,
            },
            { term: 'Criado em', value: formatDate(item.created_at) },
          ]}
        />
      </Card>

      {isCompact ? (
        <Tabs
          label="Comunicação do item"
          selectedId={activeTab}
          onSelect={setActiveTab}
          items={[
            { id: 'conversation', label: 'Conversa', content: conversation },
            { id: 'support', label: 'Suporte interno', content: support },
          ]}
        />
      ) : (
        <div className={styles.columns}>
          {conversation}
          {support}
        </div>
      )}
    </Page>
  )
}
