import { Link } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { TextField } from '../../components/ui/TextField'
import { FilterBar, type ActiveFilter } from '../../components/data/FilterBar'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { SkeletonList } from '../../components/ui/Skeleton'
import { Page } from '../../components/layout/Page'
import { PageHeader } from '../../components/layout/PageHeader'
import { formatDate } from '../../lib/utils/format'
import {
  ORDER_LOOKUP_ERROR,
  ORDER_LOOKUP_HINT,
  applyLookupToFilters,
  classifyOrderLookup,
  formatOrderNumber,
  orderLookupChipLabel,
  type OrderLookup,
} from '../../lib/utils/orderNumber'
import { useAsync } from '../../lib/utils/useAsync'
import { useUrlFilters } from '../../lib/utils/useUrlFilters'
import type { Order } from '../../types/order'
import { fetchOrders } from './api'
import { OrderItemsTable } from './OrderItemsTable'
import styles from './OrdersListPage.module.css'

function matchesLookup(order: Order, lookup: OrderLookup): boolean {
  if (lookup.status === 'number') {
    return (
      String(order.number) === lookup.value ||
      order.items.some((item) => item.number === lookup.value)
    )
  }
  if (lookup.status === 'uuid') {
    return order.id === lookup.value || order.items.some((item) => item.id === lookup.value)
  }
  return true
}

export function OrdersListPage() {
  const filters = useUrlFilters()
  const lookupInput = filters.get('number') || filters.get('order_item_id')
  const lookup = classifyOrderLookup(lookupInput)
  const state = useAsync(fetchOrders, [])

  const orders = state.status === 'success' ? state.data : []
  const visible = orders.filter((order) => matchesLookup(order, lookup))
  const appliedFilter = lookup.status === 'number' || lookup.status === 'uuid'

  const activeFilters: ActiveFilter[] = lookupInput
    ? [
        {
          key: 'number',
          label: orderLookupChipLabel(lookupInput),
          onRemove: () => {
            filters.set('number', null)
            filters.set('order_item_id', null)
          },
        },
      ]
    : []

  return (
    <Page>
      <PageHeader title="Meus pedidos" subtitle="Tudo o que você comprou no Market Hub." />

      <FilterBar active={activeFilters} onClearAll={filters.clearAll}>
        <TextField
          label="Pedido"
          name="number"
          value={lookupInput}
          onChange={(event) => applyLookupToFilters(filters.set, event.target.value)}
          placeholder="1042 ou 1042-1"
          hint={ORDER_LOOKUP_HINT}
          error={lookup.status === 'invalid' ? ORDER_LOOKUP_ERROR : undefined}
        />
      </FilterBar>

      {state.status === 'loading' && <SkeletonList variant="card" label="Carregando pedidos..." />}
      {state.status === 'error' && <ErrorState message={state.error} onRetry={state.retry} />}
      {state.status === 'success' && orders.length === 0 && !appliedFilter && (
        <EmptyState
          title="Você ainda não fez nenhum pedido."
          description="Quando comprar algo, o acompanhamento aparece aqui."
          action={<Link to="/catalog">Ir ao catálogo</Link>}
        />
      )}
      {state.status === 'success' &&
        visible.length === 0 &&
        (orders.length > 0 || appliedFilter) && (
          <EmptyState
            title="Nenhum pedido corresponde à busca."
            description="Confira o número ou limpe o filtro."
          />
        )}

      {state.status === 'success' && visible.length > 0 && (
        <div className={styles.orderList}>
          {visible.map((order) => (
            <Link key={order.id} to={`/buyer/orders/${order.id}`} className={styles.orderLink}>
              <Card interactive>
                <div className={styles.orderHeader}>
                  <span className={styles.orderId}>Pedido {formatOrderNumber(order.number)}</span>
                  <span className={styles.orderDate}>{formatDate(order.created_at)}</span>
                </div>
                <OrderItemsTable items={order.items} />
              </Card>
            </Link>
          ))}
        </div>
      )}
    </Page>
  )
}
