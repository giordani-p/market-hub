import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { formatCurrencyBRL, formatDate, toDayEndUTC, toDayStartUTC } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import type { OrderItemStatus } from '../../types/order'
import { fetchOpsOrderItems } from './api'

const PAGE_SIZE = 20

const STATUS_OPTIONS: { value: OrderItemStatus | ''; label: string }[] = [
  { value: '', label: 'Todos os status' },
  { value: 'placed', label: 'Realizado' },
  { value: 'preparing', label: 'Em preparação' },
  { value: 'in_transit', label: 'A caminho' },
  { value: 'delivered', label: 'Entregue' },
  { value: 'cancelled', label: 'Cancelado' },
]

export function OpsOrderItemsListPage() {
  const [status, setStatus] = useState<OrderItemStatus | ''>('')
  const [sellerId, setSellerId] = useState('')
  const [orderItemId, setOrderItemId] = useState('')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const [page, setPage] = useState(1)

  const state = useAsync(
    () =>
      fetchOpsOrderItems({
        page,
        pageSize: PAGE_SIZE,
        status: status || undefined,
        sellerId: sellerId.trim() || undefined,
        orderItemId: orderItemId.trim() || undefined,
        from: fromDate ? toDayStartUTC(fromDate) : undefined,
        to: toDate ? toDayEndUTC(toDate) : undefined,
      }),
    [page, status, sellerId, orderItemId, fromDate, toDate],
  )

  function updateFilter<T>(setter: (value: T) => void) {
    return (value: T) => {
      setter(value)
      setPage(1)
    }
  }

  const total = state.status === 'success' ? state.data.total : 0
  const hasNextPage = page * PAGE_SIZE < total

  return (
    <div className="page page-wide">
      <h1>Pedidos</h1>

      <div className="filters">
        <label className="field">
          <span>Status</span>
          <select
            className="input"
            value={status}
            onChange={(event) =>
              updateFilter(setStatus)(event.target.value as OrderItemStatus | '')
            }
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <Input
          label="Seller (UUID)"
          name="sellerId"
          value={sellerId}
          onChange={(event) => updateFilter(setSellerId)(event.target.value)}
          placeholder="UUID completo do Seller"
        />
        <Input
          label="ID do item (exato)"
          name="orderItemId"
          value={orderItemId}
          onChange={(event) => updateFilter(setOrderItemId)(event.target.value)}
          placeholder="UUID completo do Order Item"
        />
        <Input
          label="De"
          name="from"
          type="date"
          value={fromDate}
          onChange={(event) => updateFilter(setFromDate)(event.target.value)}
        />
        <Input
          label="Até"
          name="to"
          type="date"
          value={toDate}
          onChange={(event) => updateFilter(setToDate)(event.target.value)}
        />
      </div>

      {state.status === 'loading' && <Spinner label="Carregando itens..." />}
      {state.status === 'error' && <ErrorState message={state.error} onRetry={state.retry} />}
      {state.status === 'success' && state.data.items.length === 0 && (
        <EmptyState title="Nenhum item encontrado." />
      )}

      {state.status === 'success' && state.data.items.length > 0 && (
        <>
          <div className="order-list">
            {state.data.items.map((item) => (
              <Link
                key={item.order_item_id}
                to={`/ops/order-items/${item.order_item_id}`}
                className="product-link"
              >
                <Card>
                  <div className="order-item-row">
                    <span>{item.product.name}</span>
                    <span className="text-muted">{item.seller.name}</span>
                    <span className="text-muted">{item.buyer.name}</span>
                    <span className="text-muted">x{item.quantity}</span>
                    <span>{formatCurrencyBRL(item.purchase_price)}</span>
                    <StatusBadge status={item.status} />
                  </div>
                  <span className="text-muted">{formatDate(item.created_at)}</span>
                </Card>
              </Link>
            ))}
          </div>

          <div className="pagination">
            <Button
              type="button"
              variant="secondary"
              disabled={page === 1}
              onClick={() => setPage((value) => value - 1)}
            >
              Anterior
            </Button>
            <span className="text-muted">
              Página {page} de {Math.max(1, Math.ceil(total / PAGE_SIZE))}
            </span>
            <Button
              type="button"
              variant="secondary"
              disabled={!hasNextPage}
              onClick={() => setPage((value) => value + 1)}
            >
              Próxima
            </Button>
          </div>
        </>
      )}
    </div>
  )
}
