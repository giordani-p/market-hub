import { useState } from 'react'
import { Button } from '../../components/ui/Button'
import { errorMessage } from '../../lib/utils/errorMessage'
import type { OrderItemStatus } from '../../types/order'
import { ORDER_ITEM_STATUS_LABELS } from '../orders/status'
import { advanceOrderItemStatus, cancelOrderItem } from './api'
import { canCancel, nextStatus, STATUS_SEQUENCE } from './statusFlow'

interface StatusActionsProps {
  itemId: string
  status: OrderItemStatus
  onChanged: () => void
}

export function StatusActions({ itemId, status, onChanged }: StatusActionsProps) {
  const [pending, setPending] = useState(false)
  const [confirmingCancel, setConfirmingCancel] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const target = nextStatus(status)
  const currentIndex = STATUS_SEQUENCE.indexOf(status)

  async function handleAdvance() {
    if (!target) {
      return
    }
    setPending(true)
    setError(null)
    try {
      await advanceOrderItemStatus(itemId, target)
      onChanged()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setPending(false)
    }
  }

  async function handleCancel() {
    setPending(true)
    setError(null)
    try {
      await cancelOrderItem(itemId)
      setConfirmingCancel(false)
      onChanged()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="status-actions">
      {status === 'cancelled' ? (
        <span className="status-cancelled-note">Este item foi cancelado.</span>
      ) : (
        <ol className="status-stepper">
          {STATUS_SEQUENCE.map((step, index) => (
            <li
              key={step}
              className={
                index < currentIndex
                  ? 'status-step status-step-done'
                  : index === currentIndex
                    ? 'status-step status-step-current'
                    : 'status-step'
              }
            >
              {ORDER_ITEM_STATUS_LABELS[step]}
            </li>
          ))}
        </ol>
      )}

      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}

      <div className="status-buttons">
        {target && (
          <Button type="button" onClick={handleAdvance} disabled={pending}>
            {pending ? 'Avançando...' : `Avançar para ${ORDER_ITEM_STATUS_LABELS[target]}`}
          </Button>
        )}

        {canCancel(status) && !confirmingCancel && (
          <Button
            type="button"
            variant="destructive"
            onClick={() => setConfirmingCancel(true)}
            disabled={pending}
          >
            Cancelar pedido
          </Button>
        )}

        {confirmingCancel && (
          <div className="confirm-inline">
            <span>Cancelar este item?</span>
            <Button type="button" variant="destructive" onClick={handleCancel} disabled={pending}>
              {pending ? 'Cancelando...' : 'Confirmar cancelamento'}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setConfirmingCancel(false)}
              disabled={pending}
            >
              Voltar
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
