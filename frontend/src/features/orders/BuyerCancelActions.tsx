import { useState } from 'react'
import { Button } from '../../components/ui/Button'
import { errorMessage } from '../../lib/utils/errorMessage'
import type { OrderItemStatus } from '../../types/order'
import { cancelOrderItem } from './api'
import { canBuyerCancel } from './status'

interface BuyerCancelActionsProps {
  itemId: string
  status: OrderItemStatus
  onChanged: () => void
}

export function BuyerCancelActions({ itemId, status, onChanged }: BuyerCancelActionsProps) {
  const [pending, setPending] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!canBuyerCancel(status)) {
    return null
  }

  async function handleCancel() {
    setPending(true)
    setError(null)
    try {
      await cancelOrderItem(itemId)
      setConfirming(false)
      onChanged()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="status-actions">
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
      <div className="status-buttons">
        {!confirming && (
          <Button
            type="button"
            variant="destructive"
            onClick={() => setConfirming(true)}
            disabled={pending}
          >
            Cancelar item
          </Button>
        )}
        {confirming && (
          <div className="confirm-inline">
            <span>Cancelar este item?</span>
            <Button type="button" variant="destructive" onClick={handleCancel} disabled={pending}>
              {pending ? 'Cancelando...' : 'Confirmar cancelamento'}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setConfirming(false)}
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
