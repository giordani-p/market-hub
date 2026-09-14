import type { Product } from './catalog'

export type OrderItemStatus = 'placed' | 'preparing' | 'in_transit' | 'delivered' | 'cancelled'

export interface BuyerOrderItem {
  id: string
  order_id: string
  offer_id: string
  quantity: number
  purchase_price: string
  status: OrderItemStatus
  created_at: string
  updated_at: string
  product: Pick<Product, 'id' | 'name'>
}

export interface Order {
  id: string
  buyer_id: string
  items: BuyerOrderItem[]
  created_at: string
  updated_at: string
}

export interface BuyerSummary {
  id: string
  name: string
}

export interface SellerOrderItemListItem {
  order_item_id: string
  product: Pick<Product, 'id' | 'name'>
  quantity: number
  purchase_price: string
  status: OrderItemStatus
  created_at: string
  buyer: BuyerSummary
  order_id: string
}

export interface SellerOrderItemListResponse {
  items: SellerOrderItemListItem[]
  page: number
  page_size: number
  total: number
}

export interface SellerOrderItemDetail {
  id: string
  offer_id: string
  quantity: number
  purchase_price: string
  status: OrderItemStatus
  created_at: string
  updated_at: string
  product: Product
  buyer: BuyerSummary
  order: { id: string; created_at: string }
}

export interface SellerOrderItemFilters {
  page?: number
  pageSize?: number
  status?: OrderItemStatus
  from?: string
  to?: string
  orderItemId?: string
}

export interface CheckoutItem {
  offer_id: string
  quantity: number
  expected_price: string
}

export interface CheckoutRequest {
  items: CheckoutItem[]
}

export type CheckoutRejectReason =
  'not_found' | 'unavailable' | 'insufficient_stock' | 'price_changed'

export interface CheckoutRejectedItem {
  offer_id: string
  reason: CheckoutRejectReason
  expected_price: string | null
  current_price: string | null
  available: boolean | null
  stock: number | null
}

export interface CheckoutRejectedBody {
  code: 'checkout_rejected'
  message: string
  items: CheckoutRejectedItem[]
}
