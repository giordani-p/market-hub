import { ORDER_ITEM_STATUS_LABELS } from '../orders/status'
import { PRIORITY_LABELS } from '../ops/priority'
import type { EffectivePriority } from '../../types/conversation'
import type { AppNotification, NotificationMetadata } from '../../types/notification'
import type { OrderItemStatus } from '../../types/order'

export interface NotificationCopy {
  title: string
  message: string
}

function orderItemStatusCopy(metadata: NotificationMetadata): NotificationCopy {
  const newStatus = metadata.new_status as OrderItemStatus
  if (newStatus === 'delivered') {
    return { title: 'Pedido entregue', message: 'Seu pedido foi entregue.' }
  }
  if (newStatus === 'cancelled') {
    return { title: 'Pedido cancelado', message: 'Seu pedido foi cancelado.' }
  }
  const label = ORDER_ITEM_STATUS_LABELS[newStatus] ?? metadata.new_status
  return {
    title: 'Status do pedido atualizado',
    message: `Seu pedido agora está "${label}".`,
  }
}

function conversationStatusCopy(): NotificationCopy {
  return {
    title: 'Conversa encerrada',
    message: 'A conversa sobre este pedido foi encerrada.',
  }
}

function conversationPriorityCopy(metadata: NotificationMetadata): NotificationCopy {
  const newPriority = metadata.new_status as EffectivePriority
  if (newPriority === 'critical') {
    return {
      title: 'Prioridade crítica',
      message: 'Uma conversa foi marcada como prioridade crítica.',
    }
  }
  const label = PRIORITY_LABELS[newPriority] ?? metadata.new_status
  return {
    title: 'Prioridade atualizada',
    message: `A prioridade da conversa mudou para "${label}".`,
  }
}

/**
 * Monta titulo/mensagem em portugues a partir de `type` + `metadata`,
 * reaproveitando os mesmos labels usados em StatusBadge/PriorityBadge --
 * mesmo padrao que o resto do app ja usa pra traduzir enum do backend.
 * `title`/`message` que vem do backend (em ingles) nunca sao exibidos.
 */
export function buildNotificationCopy(notification: AppNotification): NotificationCopy {
  switch (notification.type) {
    case 'ORDER_ITEM_STATUS_CHANGED':
      return orderItemStatusCopy(notification.metadata)
    case 'CONVERSATION_STATUS_CHANGED':
      return conversationStatusCopy()
    case 'CONVERSATION_PRIORITY_CHANGED':
      return conversationPriorityCopy(notification.metadata)
    default:
      return { title: 'Atualização', message: 'Você tem uma atualização.' }
  }
}
