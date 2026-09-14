import type { UserRole } from '../../types/auth'
import type { AppNotification } from '../../types/notification'
import type { ConversationRouteContext, OrderItemRouteContext } from './api'

export interface NotificationRouteResolvers {
  fetchOrderItem: (itemId: string) => Promise<OrderItemRouteContext>
  fetchConversation: (conversationId: string) => Promise<ConversationRouteContext>
}

/**
 * Resolve pra onde navegar ao clicar numa notificacao, seguindo a tabela da
 * secao 2 da FRONTEND_F5_SPEC (papel + entity_type -> rota). Pura o
 * bastante para testar isolada: os fetches entram por parametro, sem
 * chamar `apiRequest` nem navegar aqui dentro.
 */
export async function resolveNotificationRoute(
  role: UserRole,
  notification: Pick<AppNotification, 'entity_type' | 'entity_id'>,
  resolvers: NotificationRouteResolvers,
): Promise<string> {
  const { entity_type: entityType, entity_id: entityId } = notification

  if (role === 'ops') {
    // So CONVERSATION_PRIORITY_CHANGED chega pra Ops; entity_id ja e o conversation_id.
    return `/ops/conversations/${entityId}`
  }

  if (role === 'seller') {
    if (entityType === 'ORDER_ITEM') {
      return `/seller/orders/${entityId}`
    }
    const conversation = await resolvers.fetchConversation(entityId)
    return `/seller/orders/${conversation.order_item_id}`
  }

  // buyer
  if (entityType === 'ORDER_ITEM') {
    const item = await resolvers.fetchOrderItem(entityId)
    return `/buyer/orders/${item.order.id}/items/${entityId}`
  }
  const conversation = await resolvers.fetchConversation(entityId)
  const item = await resolvers.fetchOrderItem(conversation.order_item_id)
  return `/buyer/orders/${item.order.id}/items/${conversation.order_item_id}`
}
