import { useState } from 'react'
import { Button } from '../../components/ui/Button'
import { PriorityBadge } from '../../components/ui/PriorityBadge'
import { TextField } from '../../components/ui/TextField'
import { Dialog, DialogActions } from '../../components/overlay/Dialog'
import { FormError } from '../../components/feedback/FormError'
import { useToast } from '../../components/overlay/toast-context'
import { errorMessage } from '../../lib/utils/errorMessage'
import type { OpsConversation } from '../../types/ops'
import { applyOpsCritical, refreshOpsPriority, removeOpsCritical } from './api'
import styles from './PriorityActions.module.css'

interface PriorityActionsProps {
  conversation: OpsConversation
  /** Notifica o pai para recarregar a Conversation apos qualquer mutacao. */
  onChanged: () => void
}

export function PriorityActions({ conversation, onChanged }: PriorityActionsProps) {
  const { showToast } = useToast()
  const [pending, setPending] = useState(false)
  const [markingCritical, setMarkingCritical] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [justification, setJustification] = useState('')

  async function run(action: () => Promise<unknown>, successMessage: string) {
    setPending(true)
    setError(null)
    try {
      await action()
      showToast({ message: successMessage })
      onChanged()
      return true
    } catch (err) {
      setError(errorMessage(err))
      return false
    } finally {
      setPending(false)
    }
  }

  async function handleApplyCritical() {
    if (!justification.trim()) {
      return
    }
    const ok = await run(
      () => applyOpsCritical(conversation.id, justification.trim()),
      'Conversa marcada como critical.',
    )
    if (ok) {
      setMarkingCritical(false)
      setJustification('')
    }
  }

  return (
    <div className={styles.priorityActions}>
      <h2>Prioridade</h2>

      <p className={styles.current}>
        Prioridade atual: <PriorityBadge priority={conversation.effective_priority} />
        {conversation.ops_override === 'critical' && ' (definida pela Ops)'}
      </p>

      <FormError message={error} />

      <div className={styles.buttons}>
        <Button
          type="button"
          variant="secondary"
          onClick={() => run(() => refreshOpsPriority(conversation.id), 'Prioridade recalculada.')}
          disabled={pending}
        >
          Recalcular prioridade
        </Button>

        {conversation.ops_override === 'critical' ? (
          <Button
            type="button"
            variant="secondary"
            onClick={() =>
              run(() => removeOpsCritical(conversation.id), 'Marcação critical removida.')
            }
            disabled={pending}
          >
            Remover critical
          </Button>
        ) : (
          <Button type="button" onClick={() => setMarkingCritical(true)} disabled={pending}>
            Marcar como critical
          </Button>
        )}
      </div>

      <Dialog
        open={markingCritical}
        title="Marcar como critical"
        description="A justificativa vira um comentário interno e fica visível para o vendedor."
        onClose={() => setMarkingCritical(false)}
      >
        <div className={styles.justification}>
          <TextField
            label="Justificativa"
            name="justification"
            value={justification}
            onChange={(event) => setJustification(event.target.value)}
            placeholder="Justificativa (obrigatória)"
            maxLength={2000}
            required
          />
          <DialogActions>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setMarkingCritical(false)}
              disabled={pending}
            >
              Voltar
            </Button>
            <Button
              type="button"
              onClick={handleApplyCritical}
              loading={pending}
              disabled={!justification.trim()}
            >
              Confirmar
            </Button>
          </DialogActions>
        </div>
      </Dialog>
    </div>
  )
}
