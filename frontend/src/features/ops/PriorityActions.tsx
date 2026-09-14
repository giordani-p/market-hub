import { useState } from 'react'
import { Button } from '../../components/ui/Button'
import { errorMessage } from '../../lib/utils/errorMessage'
import type { OpsConversation } from '../../types/ops'
import { applyOpsCritical, refreshOpsPriority, removeOpsCritical } from './api'

interface PriorityActionsProps {
  conversation: OpsConversation
  /** Notifica o pai para recarregar a Conversation apos qualquer mutacao. */
  onChanged: () => void
}

export function PriorityActions({ conversation, onChanged }: PriorityActionsProps) {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [markingCritical, setMarkingCritical] = useState(false)
  const [justification, setJustification] = useState('')

  async function handleRefresh() {
    setPending(true)
    setError(null)
    try {
      await refreshOpsPriority(conversation.id)
      onChanged()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setPending(false)
    }
  }

  async function handleApplyCritical() {
    if (!justification.trim()) {
      return
    }
    setPending(true)
    setError(null)
    try {
      await applyOpsCritical(conversation.id, justification.trim())
      setMarkingCritical(false)
      setJustification('')
      onChanged()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setPending(false)
    }
  }

  async function handleRemoveCritical() {
    setPending(true)
    setError(null)
    try {
      await removeOpsCritical(conversation.id)
      onChanged()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="priority-actions">
      <h2>Prioridade</h2>

      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}

      <div className="status-buttons">
        <Button type="button" variant="secondary" onClick={handleRefresh} disabled={pending}>
          {pending ? 'Recalculando...' : 'Recalcular prioridade'}
        </Button>

        {conversation.ops_override === 'critical' ? (
          <Button type="button" variant="secondary" onClick={handleRemoveCritical} disabled={pending}>
            {pending ? 'Removendo...' : 'Remover critical'}
          </Button>
        ) : (
          !markingCritical && (
            <Button type="button" onClick={() => setMarkingCritical(true)} disabled={pending}>
              Marcar como critical
            </Button>
          )
        )}
      </div>

      {markingCritical && (
        <div className="confirm-inline">
          <input
            className="input"
            value={justification}
            onChange={(event) => setJustification(event.target.value)}
            placeholder="Justificativa (obrigatória)"
            maxLength={2000}
          />
          <Button
            type="button"
            onClick={handleApplyCritical}
            disabled={pending || !justification.trim()}
          >
            {pending ? 'Enviando...' : 'Confirmar'}
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={() => setMarkingCritical(false)}
            disabled={pending}
          >
            Voltar
          </Button>
        </div>
      )}
    </div>
  )
}
