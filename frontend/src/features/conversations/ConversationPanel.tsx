import { MessageCircle } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Button } from '../../components/ui/Button'
import { PriorityBadge } from '../../components/ui/PriorityBadge'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { errorMessage } from '../../lib/utils/errorMessage'
import { formatTime } from '../../lib/utils/format'
import type { Conversation, ConversationReason, Message } from '../../types/conversation'
import {
  closeConversation,
  fetchItemConversations,
  fetchMessages,
  openConversation,
  sendMessage,
} from './api'
import { CONVERSATION_REASON_LABELS, CONVERSATION_REASONS } from './reasons'

type ViewerRole = 'buyer' | 'seller'

function MessageBubble({ message, viewerRole }: { message: Message; viewerRole: ViewerRole }) {
  if (message.author_type === 'system') {
    return <p className="message-system">{message.content}</p>
  }
  const mine = message.author_type === viewerRole
  return (
    <div className={`message-row ${mine ? 'message-row-mine' : 'message-row-theirs'}`}>
      <div className={`message-bubble ${mine ? 'message-bubble-mine' : 'message-bubble-theirs'}`}>
        <p>{message.content}</p>
        <span className="message-time">{formatTime(message.created_at)}</span>
      </div>
    </div>
  )
}

const PANEL_TITLE: Record<ViewerRole, string> = {
  seller: 'Conversa com o comprador',
  buyer: 'Conversa com o vendedor',
}

interface ConversationPanelProps {
  itemId: string
  viewerRole: ViewerRole
}

export function ConversationPanel({ itemId, viewerRole }: ConversationPanelProps) {
  const [conversations, setConversations] = useState<Conversation[] | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [selected, setSelected] = useState<Conversation | null>(null)

  const [messages, setMessages] = useState<Message[]>([])
  const [hasOlder, setHasOlder] = useState(false)
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [messagesError, setMessagesError] = useState<string | null>(null)

  const [reason, setReason] = useState<ConversationReason>('suporte')
  const [opening, setOpening] = useState(false)
  const [openError, setOpenError] = useState<string | null>(null)

  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)
  const [closing, setClosing] = useState(false)

  const loadConversations = useCallback(() => {
    setLoadError(null)
    fetchItemConversations(itemId)
      .then((list) => {
        setConversations(list)
        // Nenhuma aberta: mostra a mais recente (mesmo fechada) para nao perder o historico.
        setSelected(list.find((conversation) => conversation.status === 'open') ?? list[0] ?? null)
      })
      .catch((err: unknown) => setLoadError(errorMessage(err)))
  }, [itemId])

  useEffect(() => {
    loadConversations()
  }, [loadConversations])

  const loadMessages = useCallback((conversationId: string, before?: string) => {
    setLoadingMessages(true)
    setMessagesError(null)
    fetchMessages(conversationId, before)
      .then((result) => {
        setMessages((prev) => (before ? [...result.items, ...prev] : result.items))
        setHasOlder(result.has_older)
      })
      .catch((err: unknown) => setMessagesError(errorMessage(err)))
      .finally(() => setLoadingMessages(false))
  }, [])

  useEffect(() => {
    if (selected) {
      setMessages([])
      loadMessages(selected.id)
    }
  }, [selected, loadMessages])

  async function handleOpenConversation() {
    setOpening(true)
    setOpenError(null)
    try {
      const conversation = await openConversation(itemId, reason)
      setConversations((prev) => [conversation, ...(prev ?? [])])
      setSelected(conversation)
    } catch (err) {
      setOpenError(errorMessage(err))
    } finally {
      setOpening(false)
    }
  }

  async function handleSend() {
    if (!selected || !draft.trim()) {
      return
    }
    setSending(true)
    setSendError(null)
    try {
      const message = await sendMessage(selected.id, draft.trim())
      setMessages((prev) => [...prev, message])
      setDraft('')
    } catch (err) {
      setSendError(errorMessage(err))
    } finally {
      setSending(false)
    }
  }

  async function handleClose() {
    if (!selected) {
      return
    }
    setClosing(true)
    try {
      const closed = await closeConversation(selected.id)
      setSelected(closed)
    } catch (err) {
      setSendError(errorMessage(err))
    } finally {
      setClosing(false)
    }
  }

  if (conversations === null && !loadError) {
    return <Spinner label="Carregando conversa..." />
  }
  if (loadError) {
    return <ErrorState message={loadError} onRetry={loadConversations} />
  }

  const openForm = (
    <div className="open-conversation-form">
      <label className="field">
        <span>Motivo</span>
        <select
          className="input"
          value={reason}
          onChange={(event) => setReason(event.target.value as ConversationReason)}
        >
          {CONVERSATION_REASONS.map((value) => (
            <option key={value} value={value}>
              {CONVERSATION_REASON_LABELS[value]}
            </option>
          ))}
        </select>
      </label>
      {openError && (
        <p className="field-error" role="alert">
          {openError}
        </p>
      )}
      <Button type="button" onClick={handleOpenConversation} disabled={opening}>
        {opening ? 'Abrindo...' : 'Iniciar conversa'}
      </Button>
    </div>
  )

  const canClose = viewerRole === 'seller'

  return (
    <div className="conversation-panel">
      <div className="conversation-panel-header">
        <h2>
          <MessageCircle size={18} aria-hidden="true" />
          {PANEL_TITLE[viewerRole]}
        </h2>
        {selected && <PriorityBadge priority={selected.effective_priority} />}
      </div>

      {!selected && (
        <div className="conversation-empty">
          <EmptyState title="Nenhuma conversa neste pedido ainda." />
          {openForm}
        </div>
      )}

      {selected && (
        <div className="thread">
          {hasOlder && (
            <Button
              type="button"
              variant="secondary"
              onClick={() => loadMessages(selected.id, messages[0]?.created_at)}
              disabled={loadingMessages}
            >
              {loadingMessages ? 'Carregando...' : 'Carregar mais antigas'}
            </Button>
          )}
          {messagesError && (
            <ErrorState message={messagesError} onRetry={() => loadMessages(selected.id)} />
          )}

          <div className="thread-messages">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} viewerRole={viewerRole} />
            ))}
          </div>

          {selected.status === 'open' ? (
            <div className="thread-composer">
              <input
                className="input"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="Escrever mensagem..."
                maxLength={2000}
              />
              <Button type="button" onClick={handleSend} disabled={sending || !draft.trim()}>
                {sending ? 'Enviando...' : 'Enviar'}
              </Button>
              {canClose && (
                <Button type="button" variant="destructive" onClick={handleClose} disabled={closing}>
                  {closing ? 'Encerrando...' : 'Encerrar conversa'}
                </Button>
              )}
            </div>
          ) : (
            <div className="conversation-closed">
              <p className="text-muted">Esta conversa está encerrada.</p>
              {openForm}
            </div>
          )}
          {sendError && (
            <p className="field-error" role="alert">
              {sendError}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
