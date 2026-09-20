import { Pagination } from '../../components/ui/Pagination'
import { PriorityBadge } from '../../components/ui/PriorityBadge'
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
import { formatCurrencyBRL, formatDateTime } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import { useDebouncedValue } from '../../lib/utils/useDebouncedValue'
import {
  ORDER_LOOKUP_ERROR,
  ORDER_LOOKUP_HINT,
  applyLookupToFilters,
  classifyOrderLookup,
  formatOrderItemNumber,
  orderLookupChipLabel,
} from '../../lib/utils/orderNumber'
import { isCompleteUuid, useUrlFilters } from '../../lib/utils/useUrlFilters'
import type { EffectivePriority } from '../../types/ops'
import { fetchOpsConversationQueue } from './api'
import { EFFECTIVE_PRIORITIES, PRIORITY_LABELS } from './priority'

const PAGE_SIZE = 20

const PRIORITY_OPTIONS = [
  { value: '', label: 'Todas as prioridades' },
  ...EFFECTIVE_PRIORITIES.map((value) => ({ value, label: PRIORITY_LABELS[value] })),
]

const FILTER_KEYS = ['effective_priority', 'seller_id', 'order_item_id', 'number']

function parsePriority(value: string): EffectivePriority | '' {
  return EFFECTIVE_PRIORITIES.includes(value as EffectivePriority)
    ? (value as EffectivePriority)
    : ''
}

export function OpsQueuePage() {
  const filters = useUrlFilters()
  const effectivePriority = parsePriority(filters.get('effective_priority'))
  const sellerId = filters.get('seller_id')
  const lookupInput = filters.get('number') || filters.get('order_item_id')
  const page = Number(filters.get('page')) || 1

  const lookup = classifyOrderLookup(lookupInput)
  const debouncedSellerId = useDebouncedValue(sellerId)
  const debouncedLookupInput = useDebouncedValue(lookupInput)
  const sellerIdIsValid = debouncedSellerId === '' || isCompleteUuid(debouncedSellerId)
  const appliedLookup = classifyOrderLookup(debouncedLookupInput)

  const state = useAsync(
    () =>
      fetchOpsConversationQueue({
        page,
        pageSize: PAGE_SIZE,
        sellerId: (sellerIdIsValid && debouncedSellerId) || undefined,
        orderItemId: appliedLookup.status === 'uuid' ? appliedLookup.value : undefined,
        number: appliedLookup.status === 'number' ? appliedLookup.value : undefined,
        effectivePriority: effectivePriority || undefined,
      }),
    [
      page,
      sellerIdIsValid,
      debouncedSellerId,
      appliedLookup.status,
      appliedLookup.value,
      effectivePriority,
    ],
  )

  const total = state.status === 'success' ? state.data.total : 0
  const items = state.status === 'success' ? state.data.items : []
  const hasFilters = filters.countActive(FILTER_KEYS) > 0

  const activeFilters: ActiveFilter[] = [
    ...(effectivePriority
      ? [
          {
            key: 'effective_priority',
            label: PRIORITY_LABELS[effectivePriority],
            onRemove: () => filters.set('effective_priority', null),
          },
        ]
      : []),
    ...(sellerId
      ? [
          {
            key: 'seller_id',
            label: items.find((item) => item.seller.id === sellerId)?.seller.name ?? 'Vendedor',
            onRemove: () => filters.set('seller_id', null),
          },
        ]
      : []),
    ...(lookupInput
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
      : []),
  ]

  return (
    <Page width="wide">
      <PageHeader
        title="Fila de atendimento"
        subtitle="Conversas abertas, da mais urgente para a menos urgente. A ordem vem do backend."
      />

      <FilterBar active={activeFilters} onClearAll={filters.clearAll}>
        <SelectField
          label="Prioridade"
          name="effective_priority"
          value={effectivePriority}
          options={PRIORITY_OPTIONS}
          onChange={(event) => filters.set('effective_priority', event.target.value || null)}
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
          label="Pedido"
          name="number"
          value={lookupInput}
          onChange={(event) => applyLookupToFilters(filters.set, event.target.value)}
          placeholder="1042 ou 1042-1"
          hint={ORDER_LOOKUP_HINT}
          error={lookup.status === 'invalid' ? ORDER_LOOKUP_ERROR : undefined}
        />
      </FilterBar>

      {state.status === 'loading' && <SkeletonList variant="row" label="Carregando fila..." />}
      {state.status === 'error' && <ErrorState message={state.error} onRetry={state.retry} />}
      {state.status === 'success' && items.length === 0 && !hasFilters && (
        <EmptyState
          title="Nenhuma conversa em aberto."
          description="Nada na fila agora. Conversas novas entram aqui já classificadas."
        />
      )}
      {state.status === 'success' && items.length === 0 && hasFilters && (
        <EmptyState
          title="Nenhuma conversa corresponde aos filtros."
          description="Remova um filtro para ver a fila completa."
        />
      )}

      {state.status === 'success' && items.length > 0 && (
        <>
          <Table caption="Conversas abertas por prioridade">
            <TableHead>
              <TableRow>
                <TableHeaderCell>Prioridade</TableHeaderCell>
                <TableHeaderCell>Pedido</TableHeaderCell>
                <TableHeaderCell>Produto</TableHeaderCell>
                <TableHeaderCell>Vendedor</TableHeaderCell>
                <TableHeaderCell>Comprador</TableHeaderCell>
                <TableHeaderCell numeric>Valor</TableHeaderCell>
                <TableHeaderCell>Status do item</TableHeaderCell>
                <TableHeaderCell>Última interação</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {items.map((item) => (
                <TableRow key={item.id} linked>
                  <TableCell label="Prioridade">
                    <PriorityBadge priority={item.effective_priority} />
                  </TableCell>
                  <TableCell label="Pedido">{formatOrderItemNumber(item.number)}</TableCell>
                  <TableCell label="Produto">
                    <TableRowLink to={`/ops/conversations/${item.id}`}>
                      {item.product.name}
                    </TableRowLink>
                  </TableCell>
                  <TableCell label="Vendedor">{item.seller.name}</TableCell>
                  <TableCell label="Comprador">{item.buyer.name}</TableCell>
                  <TableCell label="Valor" numeric>
                    {formatCurrencyBRL(item.purchase_price)}
                  </TableCell>
                  <TableCell label="Status do item">
                    <StatusBadge status={item.order_item_status} />
                  </TableCell>
                  <TableCell label="Última interação">
                    {formatDateTime(item.last_interaction_at)}
                  </TableCell>
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
