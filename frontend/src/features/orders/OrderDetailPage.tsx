import { useParams } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { Page } from '../../components/layout/Page'
import { PageHeader } from '../../components/layout/PageHeader'
import { formatDate } from '../../lib/utils/format'
import { formatOrderNumber } from '../../lib/utils/orderNumber'
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
    <Page>
      <PageHeader
        title={`Pedido ${formatOrderNumber(order.number)}`}
        subtitle={`Criado em ${formatDate(order.created_at)}`}
        breadcrumbs={[
          { label: 'Meus pedidos', to: '/buyer/orders' },
          { label: formatOrderNumber(order.number) },
        ]}
      />
      <Card>
        <OrderItemsTable items={order.items} orderId={order.id} />
      </Card>
    </Page>
  )
}
