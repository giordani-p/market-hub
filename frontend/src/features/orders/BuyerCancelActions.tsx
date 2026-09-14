import { useState } from 'react'
import { Button } from '../../components/ui/Button'
import { ConfirmDialog } from '../../components/overlay/ConfirmDialog'
import { FormError } from '../../components/feedback/FormError'
import { useToast } from '../../components/overlay/toast-context'
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
  const { showToast } = useToast()
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
      showToast({ message: 'Item cancelado.' })
      onChanged()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setPending(false)
    }
  }

  return (
    <>
      <FormError message={error} />
      <Button
        type="button"
        variant="destructive"
        onClick={() => setConfirming(true)}
        disabled={pending}
      >
        Cancelar item
      </Button>

      <ConfirmDialog
        open={confirming}
        title="Cancelar este item?"
        description="O cancelamento não pode ser desfeito."
        confirmLabel="Confirmar cancelamento"
        destructive
        pending={pending}
        onConfirm={handleCancel}
        onCancel={() => setConfirming(false)}
      />
    </>
  )
}
