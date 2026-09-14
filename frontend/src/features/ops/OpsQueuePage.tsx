import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { PriorityBadge } from '../../components/ui/PriorityBadge'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { formatCurrencyBRL } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import type { EffectivePriority } from '../../types/ops'
import { fetchOpsConversationQueue } from './api'
import { EFFECTIVE_PRIORITIES, PRIORITY_LABELS } from './priority'

const PAGE_SIZE = 20

const PRIORITY_OPTIONS: { value: EffectivePriority | ''; label: string }[] = [
  { value: '', label: 'Todas as prioridades' },
  ...EFFECTIVE_PRIORITIES.map((value) => ({ value, label: PRIORITY_LABELS[value] })),
]

function parsePriority(value: string | null): EffectivePriority | '' {
  return value && EFFECTIVE_PRIORITIES.includes(value as EffectivePriority)
    ? (value as EffectivePriority)
    : ''
}

export function OpsQueuePage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const effectivePriority = parsePriority(searchParams.get('effective_priority'))
  const [sellerId, setSellerId] = useState('')
  const [orderItemId, setOrderItemId] = useState('')
  const [page, setPage] = useState(1)

  const state = useAsync(
    () =>
      fetchOpsConversationQueue({
        page,
        pageSize: PAGE_SIZE,
        sellerId: sellerId.trim() || undefined,
        orderItemId: orderItemId.trim() || undefined,
        effectivePriority: effectivePriority || undefined,
      }),
    [page, sellerId, orderItemId, effectivePriority],
  )

  function updateFilter<T>(setter: (value: T) => void) {
    return (value: T) => {
      setter(value)
      setPage(1)
    }
  }

  function updatePriority(value: EffectivePriority | '') {
    setSearchParams(
      (current) => {
        const next = new URLSearchParams(current)
        if (value) {
          next.set('effective_priority', value)
        } else {
          next.delete('effective_priority')
        }
        return next
      },
      { replace: true },
    )
    setPage(1)
  }

  const total = state.status === 'success' ? state.data.total : 0
  const hasNextPage = page * PAGE_SIZE < total

  return (
    <div className="page page-wide">
      <h1>Fila de Ops</h1>

      <div className="filters">
        <Input
          label="Seller (UUID)"
          name="sellerId"
          value={sellerId}
          onChange={(event) => updateFilter(setSellerId)(event.target.value)}
          placeholder="UUID completo do Seller"
        />
        <Input
          label="Order Item (UUID)"
          name="orderItemId"
          value={orderItemId}
          onChange={(event) => updateFilter(setOrderItemId)(event.target.value)}
          placeholder="UUID completo do Order Item"
        />
        <label className="field">
          <span>Prioridade</span>
          <select
            className="input"
            value={effectivePriority}
            onChange={(event) =>
              updatePriority(event.target.value as EffectivePriority | '')
            }
          >
            {PRIORITY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {state.status === 'loading' && <Spinner label="Carregando fila..." />}
      {state.status === 'error' && <ErrorState message={state.error} onRetry={state.retry} />}
      {state.status === 'success' && state.data.items.length === 0 && (
        <EmptyState title="Nenhuma conversa em aberto." />
      )}

      {state.status === 'success' && state.data.items.length > 0 && (
        <>
          <div className="order-list">
            {state.data.items.map((item) => (
              <Link key={item.id} to={`/ops/conversations/${item.id}`} className="product-link">
                <Card>
                  <div className="order-item-row">
                    <span>{item.product.name}</span>
                    <span className="text-muted">{item.seller.name}</span>
                    <span className="text-muted">{item.buyer.name}</span>
                    <span>{formatCurrencyBRL(item.purchase_price)}</span>
                    <StatusBadge status={item.order_item_status} />
                    <PriorityBadge priority={item.effective_priority} />
                  </div>
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
