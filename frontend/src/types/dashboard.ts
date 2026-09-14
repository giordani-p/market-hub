import type { EffectivePriority } from './conversation'
import type { BuyerSummary, OrderItemStatus } from './order'
import type { SellerSummary } from './ops'

export type BuyerOrderProjectionStatus = 'in_progress' | 'completed' | 'cancelled'

export interface OrderItemsByStatus {
  placed: number
  preparing: number
  in_transit: number
  delivered: number
  cancelled: number
}

export interface ConversationsByPriority {
  critical: number
  high: number
  medium: number
  low: number
}

export interface OpenConversationsAttention {
  open_conversations: number
}

export interface SellerDashboardSummary {
  total_order_items: number
  active_order_items: number
  order_items_by_status: OrderItemsByStatus
}

export interface SellerRecentOrderItem {
  order_item_id: string
  order_id: string
  product: { id: string; name: string }
  buyer: BuyerSummary
  quantity: number
  purchase_price: string
  status: OrderItemStatus
  created_at: string
}

export interface SellerDashboard {
  role: 'seller'
  summary: SellerDashboardSummary
  attention: OpenConversationsAttention
  recent: { order_items: SellerRecentOrderItem[] }
}

export interface BuyerDashboardSummary {
  active_orders: number
  completed_orders: number
}

export interface BuyerRecentOrderItem {
  order_item_id: string
  product: { id: string; name: string }
  quantity: number
  status: OrderItemStatus
}

export interface BuyerRecentOrder {
  order_id: string
  created_at: string
  status: BuyerOrderProjectionStatus
  total_amount: string
  items: BuyerRecentOrderItem[]
}

export interface BuyerDashboard {
  role: 'buyer'
  summary: BuyerDashboardSummary
  attention: OpenConversationsAttention
  recent: { orders: BuyerRecentOrder[] }
}

export interface OpsDashboardSummary {
  open_conversations: number
  conversations_by_priority: ConversationsByPriority
}

export interface OpsQueuePreviewItem {
  conversation_id: string
  order_item_id: string
  effective_priority: EffectivePriority
  calculated_priority: string
  ops_override: string | null
  reason: string
  last_interaction_at: string
  seller: SellerSummary
  buyer: BuyerSummary
  product: { id: string; name: string }
  order_item_status: OrderItemStatus
  purchase_price: string
}

export interface OpsDashboard {
  role: 'ops'
  summary: OpsDashboardSummary
  attention: { priority_queue_preview: OpsQueuePreviewItem[] }
  recent: Record<string, never>
}

export type DashboardResponse = SellerDashboard | BuyerDashboard | OpsDashboard
