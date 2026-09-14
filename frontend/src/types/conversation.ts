export type ConversationStatus = 'open' | 'closed'

export type ConversationReason =
  'atraso' | 'troca' | 'devolucao' | 'reclamacao' | 'suporte' | 'elogio' | 'outros'

/** Resultado final da PriorityPolicy. Buyer/Seller so veem isto -- nunca o
 *  breakdown (calculated_priority/ops_override), que e exclusivo da Ops. */
export type EffectivePriority = 'low' | 'medium' | 'high' | 'critical'

export interface Conversation {
  id: string
  order_item_id: string
  reason: string
  status: ConversationStatus
  created_at: string
  updated_at: string
  last_interaction_at: string
  effective_priority: EffectivePriority
}

export type MessageAuthorType = 'buyer' | 'seller' | 'system'

export interface Message {
  id: string
  conversation_id: string
  author_type: MessageAuthorType
  author_user_id: string | null
  content: string
  created_at: string
}

export interface MessageListResponse {
  items: Message[]
  from: string
  to: string
  has_older: boolean
}
