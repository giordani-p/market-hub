import { Pagination } from '../../components/ui/Pagination'
import { SelectField } from '../../components/ui/SelectField'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { TextField } from '../../components/ui/TextField'
import { FilterBar, type ActiveFilter } from '../../components/data/FilterBar'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
  TableRowLink,
} from '../../components/data/Table'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { SkeletonList } from '../../components/ui/Skeleton'
import { Page } from '../../components/layout/Page'
import { PageHeader } from '../../components/layout/PageHeader'
import { formatCurrencyBRL, formatDate, toDayEndUTC, toDayStartUTC } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import { useDebouncedValue } from '../../lib/utils/useDebouncedValue'
import { isCompleteUuid, useUrlFilters } from '../../lib/utils/useUrlFilters'
import type { OrderItemStatus } from '../../types/order'
import { ORDER_ITEM_STATUS_LABELS } from '../orders/status'
import { fetchOpsOrderItems } from './api'

const PAGE_SIZE = 20

const STATUS_VALUES: OrderItemStatus[] = [
  'placed',
  'preparing',
  'in_transit',
  'delivered',
  'cancelled',
]

const STATUS_OPTIONS = [
  { value: '', label: 'Todos os status' },
  ...STATUS_VALUES.map((value) => ({ value, label: ORDER_ITEM_STATUS_LABELS[value] })),
]

const FILTER_KEYS = ['status', 'seller_id', 'order_item_id', 'from', 'to']

function parseStatus(value: string): OrderItemStatus | '' {
  return STATUS_VALUES.includes(value as OrderItemStatus) ? (value as OrderItemStatus) : ''
}

export function OpsOrderItemsListPage() {
  const filters = useUrlFilters()
  const status = parseStatus(filters.get('status'))
  const sellerId = filters.get('seller_id')
  const orderItemId = filters.get('order_item_id')
  const fromDate = filters.get('from')
  const toDate = filters.get('to')
  const page = Number(filters.get('page')) || 1

  const debouncedSellerId = useDebouncedValue(sellerId)
  const debouncedOrderItemId = useDebouncedValue(orderItemId)
  const sellerIdIsValid = debouncedSellerId === '' || isCompleteUuid(debouncedSellerId)
  const orderItemIdIsValid = debouncedOrderItemId === '' || isCompleteUuid(debouncedOrderItemId)

  const state = useAsync(
    () =>
      fetchOpsOrderItems({
        page,
        pageSize: PAGE_SIZE,
        status: status || undefined,
        sellerId: (sellerIdIsValid && debouncedSellerId) || undefined,
        orderItemId: (orderItemIdIsValid && debouncedOrderItemId) || undefined,
        from: fromDate ? toDayStartUTC(fromDate) : undefined,
        to: toDate ? toDayEndUTC(toDate) : undefined,
      }),
    [
      page,
      status,
      sellerIdIsValid,
      debouncedSellerId,
      orderItemIdIsValid,
      debouncedOrderItemId,
      fromDate,
      toDate,
    ],
  )

  const total = state.status === 'success' ? state.data.total : 0
  const items = state.status === 'success' ? state.data.items : []
  const hasFilters = filters.countActive(FILTER_KEYS) > 0

  const activeFilters: ActiveFilter[] = [
    ...(status
      ? [
          {
            key: 'status',
            label: ORDER_ITEM_STATUS_LABELS[status],
            onRemove: () => filters.set('status', null),
          },
        ]
      : []),
    ...(sellerId
      ? [
          {
            key: 'seller_id',
            label: `Vendedor ${sellerId.slice(0, 8)}`,
            onRemove: () => filters.set('seller_id', null),
          },
        ]
      : []),
    ...(orderItemId
      ? [
          {
            key: 'order_item_id',
            label: `Item ${orderItemId.slice(0, 8)}`,
            onRemove: () => filters.set('order_item_id', null),
          },
        ]
      : []),
    ...(fromDate
      ? [{ key: 'from', label: `De ${fromDate}`, onRemove: () => filters.set('from', null) }]
      : []),
    ...(toDate
      ? [{ key: 'to', label: `Até ${toDate}`, onRemove: () => filters.set('to', null) }]
      : []),
  ]

  return (
    <Page width="wide">
      <PageHeader
        title="Pedidos"
        subtitle="Todos os itens da operação, com ou sem conversa aberta."
      />

      <FilterBar active={activeFilters} onClearAll={filters.clearAll}>
        <SelectField
          label="Status"
          name="status"
          value={status}
          options={STATUS_OPTIONS}
          onChange={(event) => filters.set('status', event.target.value || null)}
        />
        <TextField
          label="Vendedor"
          name="seller_id"
          value={sellerId}
          onChange={(event) => filters.set('seller_id', event.target.value || null)}
          placeholder="00000000-0000-0000-0000-000000000000"
          hint="Cole o ID completo do vendedor."
          error={sellerIdIsValid ? undefined : 'Informe o ID completo do vendedor.'}
        />
        <TextField
          label="Item do pedido"
          name="order_item_id"
          value={orderItemId}
          onChange={(event) => filters.set('order_item_id', event.target.value || null)}
          placeholder="00000000-0000-0000-0000-000000000000"
          hint="Cole o ID completo do item."
          error={orderItemIdIsValid ? undefined : 'Informe o ID completo do item.'}
        />
        <TextField
          label="De"
          name="from"
          type="date"
          value={fromDate}
          onChange={(event) => filters.set('from', event.target.value || null)}
        />
        <TextField
          label="Até"
          name="to"
          type="date"
          value={toDate}
          onChange={(event) => filters.set('to', event.target.value || null)}
        />
      </FilterBar>

      {state.status === 'loading' && <SkeletonList variant="row" label="Carregando itens..." />}
      {state.status === 'error' && <ErrorState message={state.error} onRetry={state.retry} />}
      {state.status === 'success' && items.length === 0 && !hasFilters && (
        <EmptyState title="Nenhum item encontrado." />
      )}
      {state.status === 'success' && items.length === 0 && hasFilters && (
        <EmptyState
          title="Nenhum item corresponde aos filtros."
          description="Remova um filtro ou amplie o intervalo de datas."
        />
      )}

      {state.status === 'success' && items.length > 0 && (
        <>
          <Table caption="Itens de pedido da operação">
            <TableHead>
              <TableRow>
                <TableHeaderCell>Produto</TableHeaderCell>
                <TableHeaderCell>Vendedor</TableHeaderCell>
                <TableHeaderCell>Comprador</TableHeaderCell>
                <TableHeaderCell numeric>Qtd</TableHeaderCell>
                <TableHeaderCell numeric>Valor</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Data</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {items.map((item) => (
                <TableRow key={item.order_item_id} linked>
                  <TableCell label="Produto">
                    <TableRowLink to={`/ops/order-items/${item.order_item_id}`}>
                      {item.product.name}
                    </TableRowLink>
                  </TableCell>
                  <TableCell label="Vendedor">{item.seller.name}</TableCell>
                  <TableCell label="Comprador">{item.buyer.name}</TableCell>
                  <TableCell label="Qtd" numeric>
                    {item.quantity}
                  </TableCell>
                  <TableCell label="Valor" numeric>
                    {formatCurrencyBRL(item.purchase_price)}
                  </TableCell>
                  <TableCell label="Status">
                    <StatusBadge status={item.status} />
                  </TableCell>
                  <TableCell label="Data">{formatDate(item.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <Pagination
            page={page}
            pageSize={PAGE_SIZE}
            total={total}
            onPageChange={(next) => filters.set('page', String(next))}
          />
        </>
      )}
    </Page>
  )
}
