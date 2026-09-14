export type NotificationType =
  'ORDER_ITEM_STATUS_CHANGED' | 'CONVERSATION_STATUS_CHANGED' | 'CONVERSATION_PRIORITY_CHANGED'

export type NotificationEntityType = 'ORDER_ITEM' | 'CONVERSATION'

export interface NotificationMetadata {
  previous_status: string
  new_status: string
}

/** Nomeado AppNotification para nao colidir com a `Notification` global do browser. */
export interface AppNotification {
  id: string
  recipient_id: string
  type: NotificationType
  title: string
  message: string
  entity_type: NotificationEntityType
  entity_id: string
  metadata: NotificationMetadata
  created_at: string
  read_at: string | null
}

export interface NotificationListResponse {
  items: AppNotification[]
  page: number
  page_size: number
  total: number
}

export interface UnreadCountResponse {
  unread_count: number
}
