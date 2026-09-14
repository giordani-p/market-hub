import { useState } from 'react'
import { Button } from '../../components/ui/Button'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { errorMessage } from '../../lib/utils/errorMessage'
import { formatDateTime } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import { createInternalComment, fetchInternalComments } from './api'

type ViewerRole = 'seller' | 'ops'

const PANEL_DESCRIPTION: Record<ViewerRole, string> = {
  seller: 'Canal entre você e a Ops — o comprador não vê isto.',
  ops: 'Canal entre você e o Seller — o comprador não vê isto.',
}

/** Rotulo de quem escreveu, quando nao e o proprio viewer. */
const OTHER_AUTHOR_LABEL: Record<ViewerRole, string> = {
  seller: 'Ops',
  ops: 'Seller',
}

interface InternalCommentsPanelProps {
  itemId: string
  viewerRole?: ViewerRole
}

export function InternalCommentsPanel({ itemId, viewerRole = 'seller' }: InternalCommentsPanelProps) {
  const state = useAsync(() => fetchInternalComments(itemId, viewerRole), [itemId, viewerRole])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)

  async function handleSend() {
    if (!draft.trim()) {
      return
    }
    setSending(true)
    setSendError(null)
    try {
      await createInternalComment(itemId, draft.trim(), viewerRole)
      setDraft('')
      state.retry()
    } catch (err) {
      setSendError(errorMessage(err))
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="support-log">
      <h2>Suporte interno</h2>
      <p className="text-muted">{PANEL_DESCRIPTION[viewerRole]}</p>

      {state.status === 'loading' && <Spinner label="Carregando comentários..." />}
      {state.status === 'error' && <ErrorState message={state.error} onRetry={state.retry} />}
      {state.status === 'success' && state.data.length === 0 && (
        <EmptyState title="Nenhum comentário interno ainda." />
      )}

      {state.status === 'success' && state.data.length > 0 && (
        <ul className="support-entries">
          {state.data.map((comment) => (
            <li key={comment.id} className="support-entry">
              <span className="support-entry-time">{formatDateTime(comment.created_at)}</span>
              <span className="support-entry-author">
                {comment.author_type === viewerRole ? 'Você' : OTHER_AUTHOR_LABEL[viewerRole]}
              </span>
              <span className="support-entry-content">{comment.content}</span>
            </li>
          ))}
        </ul>
      )}

      <div className="support-composer">
        <input
          className="input"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Registrar comentário interno..."
          maxLength={2000}
        />
        <Button type="button" onClick={handleSend} disabled={sending || !draft.trim()}>
          {sending ? 'Enviando...' : 'Registrar'}
        </Button>
      </div>
      {sendError && (
        <p className="field-error" role="alert">
          {sendError}
        </p>
      )}
    </div>
  )
}
