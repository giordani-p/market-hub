import type { Product } from './catalog'
import type { EffectivePriority } from './conversation'
import type { BuyerSummary, OrderItemStatus } from './order'

export type { EffectivePriority }
export type CalculatedPriority = 'low' | 'medium' | 'high'
export type OpsOverride = 'critical' | null

export type ConversationStatus = 'open' | 'closed'

export interface SellerSummary {
  id: string
  name: string
}

export interface OpsConversation {
  id: string
  order_item_id: string
  reason: string
  status: ConversationStatus
  created_at: string
  updated_at: string
  last_interaction_at: string
  calculated_priority: CalculatedPriority
  ops_override: OpsOverride
  effective_priority: EffectivePriority
}

export interface OpsConversationQueueItem extends OpsConversation {
  seller: SellerSummary
  product: Pick<Product, 'id' | 'name'>
  buyer: BuyerSummary
  order_item_status: OrderItemStatus
  purchase_price: string
}

export interface OpsConversationQueueResponse {
  items: OpsConversationQueueItem[]
  page: number
  page_size: number
  total: number
}

export interface OpsConversationQueueFilters {
  page?: number
  pageSize?: number
  sellerId?: string
  orderItemId?: string
  effectivePriority?: EffectivePriority
}

export interface OpsOrderItemDetail {
  id: string
  offer_id: string
  quantity: number
  purchase_price: string
  status: OrderItemStatus
  created_at: string
  updated_at: string
  product: Product
  buyer: BuyerSummary
  seller: SellerSummary
  order: { id: string; created_at: string }
}
