import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../../components/ui/Button'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { errorMessage } from '../../lib/utils/errorMessage'
import { formatDateTime } from '../../lib/utils/format'
import type { UserRole } from '../../types/auth'
import type { AppNotification } from '../../types/notification'
import {
  fetchConversationRouteContext,
  fetchNotifications,
  fetchOrderItemRouteContext,
  fetchUnreadCount,
  markAllNotificationsRead,
  markNotificationRead,
} from './api'
import { resolveNotificationRoute } from './resolveRoute'

const PAGE_SIZE = 10

export function NotificationBell({ role }: { role: UserRole }) {
  const navigate = useNavigate()
  const [unreadCount, setUnreadCount] = useState(0)
  const [open, setOpen] = useState(false)

  const [notifications, setNotifications] = useState<AppNotification[] | null>(null)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [markingAll, setMarkingAll] = useState(false)

  const loadUnreadCount = useCallback(() => {
    fetchUnreadCount()
      .then((result) => setUnreadCount(result.unread_count))
      .catch(() => {
        // contagem e so um indicador -- falha aqui nao deve travar o header.
      })
  }, [])

  useEffect(() => {
    loadUnreadCount()
  }, [loadUnreadCount])

  const loadNotifications = useCallback((targetPage: number) => {
    setLoading(true)
    setLoadError(null)
    fetchNotifications({ page: targetPage, pageSize: PAGE_SIZE })
      .then((result) => {
        setNotifications((prev) =>
          targetPage === 1 ? result.items : [...(prev ?? []), ...result.items],
        )
        setTotal(result.total)
        setPage(targetPage)
      })
      .catch((err: unknown) => setLoadError(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [])

  function handleToggle() {
    const next = !open
    setOpen(next)
    if (next && notifications === null) {
      loadNotifications(1)
    }
  }

  async function handleMarkAll() {
    setMarkingAll(true)
    try {
      await markAllNotificationsRead()
      setUnreadCount(0)
      setNotifications((prev) => prev?.map((n) => ({ ...n, read_at: n.read_at ?? new Date().toISOString() })) ?? null)
    } catch {
      // botao continua disponivel para nova tentativa; nao trava o dropdown.
    } finally {
      setMarkingAll(false)
    }
  }

  async function handleSelect(notification: AppNotification) {
    if (!notification.read_at) {
      setNotifications((prev) =>
        prev?.map((n) => (n.id === notification.id ? { ...n, read_at: new Date().toISOString() } : n)) ?? null,
      )
      setUnreadCount((count) => Math.max(0, count - 1))
      markNotificationRead(notification.id).catch(() => {
        // marcar como lida nao deve bloquear a navegacao a seguir.
      })
    }
    setOpen(false)
    try {
      const path = await resolveNotificationRoute(role, notification, {
        fetchOrderItem: fetchOrderItemRouteContext,
        fetchConversation: fetchConversationRouteContext,
      })
      navigate(path)
    } catch {
      // entidade pode ja nao existir mais (ex.: item removido) -- fica na tela atual.
    }
  }

  const hasOlder = notifications !== null && notifications.length < total

  return (
    <div className="notification-bell">
      <button
        type="button"
        className="notification-trigger"
        onClick={handleToggle}
        aria-label={unreadCount > 0 ? `${unreadCount} notificações não lidas` : 'Notificações'}
        aria-expanded={open}
      >
        <span aria-hidden="true">🔔</span>
        {unreadCount > 0 && <span className="notification-badge">{unreadCount}</span>}
      </button>

      {open && (
        <div className="notification-dropdown">
          <div className="notification-dropdown-header">
            <h2>Notificações</h2>
            <Button
              type="button"
              variant="secondary"
              onClick={handleMarkAll}
              disabled={markingAll || unreadCount === 0}
            >
              {markingAll ? 'Marcando...' : 'Marcar todas como lidas'}
            </Button>
          </div>

          {notifications === null && loading && <Spinner label="Carregando notificações..." />}
          {loadError && (
            <ErrorState message={loadError} onRetry={() => loadNotifications(1)} />
          )}
          {notifications !== null && notifications.length === 0 && !loadError && (
            <EmptyState title="Nenhuma notificação ainda." />
          )}

          {notifications !== null && notifications.length > 0 && (
            <ul className="notification-list">
              {notifications.map((notification) => (
                <li key={notification.id}>
                  <button
                    type="button"
                    className={`notification-item${notification.read_at ? '' : ' notification-item-unread'}`}
                    onClick={() => handleSelect(notification)}
                  >
                    <span className="notification-item-title">{notification.title}</span>
                    <span className="notification-item-message">{notification.message}</span>
                    <span className="notification-item-time">
                      {formatDateTime(notification.created_at)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}

          {hasOlder && (
            <Button
              type="button"
              variant="secondary"
              onClick={() => loadNotifications(page + 1)}
              disabled={loading}
            >
              {loading ? 'Carregando...' : 'Carregar mais'}
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
