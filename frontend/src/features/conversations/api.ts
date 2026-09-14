import { apiRequest } from '../../lib/api/client'
import type {
  Conversation,
  ConversationReason,
  Message,
  MessageListResponse,
} from '../../types/conversation'

export function fetchItemConversations(itemId: string): Promise<Conversation[]> {
  return apiRequest<Conversation[]>(`/order-items/${itemId}/conversations`)
}

export function openConversation(
  itemId: string,
  reason: ConversationReason,
): Promise<Conversation> {
  return apiRequest<Conversation>(`/order-items/${itemId}/conversation`, {
    method: 'POST',
    body: { reason },
  })
}

export function fetchMessages(
  conversationId: string,
  before?: string,
): Promise<MessageListResponse> {
  const query = before ? `?before=${encodeURIComponent(before)}` : ''
  return apiRequest<MessageListResponse>(`/conversations/${conversationId}/messages${query}`)
}

export function sendMessage(conversationId: string, content: string): Promise<Message> {
  return apiRequest<Message>(`/conversations/${conversationId}/messages`, {
    method: 'POST',
    body: { content },
  })
}

export function closeConversation(conversationId: string): Promise<Conversation> {
  return apiRequest<Conversation>(`/conversations/${conversationId}/close`, { method: 'POST' })
}
