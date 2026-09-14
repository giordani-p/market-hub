import { XCircle } from 'lucide-react'
import { useState } from 'react'
import { Button } from '../../components/ui/Button'
import { ConfirmDialog } from '../../components/overlay/ConfirmDialog'
import { FormError } from '../../components/feedback/FormError'
import { useToast } from '../../components/overlay/toast-context'
import { errorMessage } from '../../lib/utils/errorMessage'
import type { OrderItemStatus } from '../../types/order'
import { ORDER_ITEM_STATUS_LABELS } from '../orders/status'
import { advanceOrderItemStatus, cancelOrderItem } from './api'
import { canCancel, nextStatus, STATUS_SEQUENCE } from './statusFlow'
import styles from './StatusActions.module.css'

interface StatusActionsProps {
  itemId: string
  status: OrderItemStatus
  onChanged: () => void
}

export function StatusActions({ itemId, status, onChanged }: StatusActionsProps) {
  const { showToast } = useToast()
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
      showToast({ message: `Status atualizado para ${ORDER_ITEM_STATUS_LABELS[target]}.` })
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
      showToast({ message: 'Pedido cancelado.' })
      onChanged()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setPending(false)
    }
  }

  return (
    <div className={styles.statusActions}>
      {status === 'cancelled' ? (
        <p className={styles.cancelledNote}>
          <XCircle size={18} aria-hidden="true" />
          Este item foi cancelado.
        </p>
      ) : (
        <ol className={styles.stepper}>
          {STATUS_SEQUENCE.map((step, index) => {
            const stepClass =
              index < currentIndex
                ? styles.stepDone
                : index === currentIndex
                  ? styles.stepCurrent
                  : ''
            return (
              <li
                key={step}
                className={`${styles.step} ${stepClass}`.trim()}
                aria-current={index === currentIndex ? 'step' : undefined}
              >
                {ORDER_ITEM_STATUS_LABELS[step]}
              </li>
            )
          })}
        </ol>
      )}

      <FormError message={error} />

      <div className={styles.buttons}>
        {target && (
          <Button type="button" onClick={handleAdvance} loading={pending}>
            Avançar para {ORDER_ITEM_STATUS_LABELS[target]}
          </Button>
        )}

        {canCancel(status) && (
          <Button
            type="button"
            variant="destructive"
            onClick={() => setConfirmingCancel(true)}
            disabled={pending}
          >
            Cancelar pedido
          </Button>
        )}
      </div>

      <ConfirmDialog
        open={confirmingCancel}
        title="Cancelar este item?"
        description="O comprador é notificado e o cancelamento não pode ser desfeito."
        confirmLabel="Confirmar cancelamento"
        destructive
        pending={pending}
        onConfirm={handleCancel}
        onCancel={() => setConfirmingCancel(false)}
      />
    </div>
  )
}
