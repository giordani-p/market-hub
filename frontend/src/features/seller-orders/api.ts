import { apiRequest } from '../../lib/api/client'
import type {
  SellerOrderItemDetail,
  SellerOrderItemFilters,
  SellerOrderItemListResponse,
} from '../../types/order'

export function buildSellerOrderItemsQuery(filters: SellerOrderItemFilters): string {
  const params = new URLSearchParams()
  if (filters.page !== undefined) {
    params.set('page', String(filters.page))
  }
  if (filters.pageSize !== undefined) {
    params.set('page_size', String(filters.pageSize))
  }
  if (filters.status) {
    params.set('status', filters.status)
  }
  if (filters.from) {
    params.set('from', filters.from)
  }
  if (filters.to) {
    params.set('to', filters.to)
  }
  if (filters.orderItemId) {
    params.set('order_item_id', filters.orderItemId)
  }
  const query = params.toString()
  return query ? `?${query}` : ''
}

export function fetchSellerOrderItems(
  filters: SellerOrderItemFilters,
): Promise<SellerOrderItemListResponse> {
  return apiRequest<SellerOrderItemListResponse>(
    `/order-items${buildSellerOrderItemsQuery(filters)}`,
  )
}

export function fetchSellerOrderItem(itemId: string): Promise<SellerOrderItemDetail> {
  return apiRequest<SellerOrderItemDetail>(`/order-items/${itemId}`)
}
