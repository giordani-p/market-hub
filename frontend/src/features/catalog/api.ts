import { apiRequest } from '../../lib/api/client'
import type { Offer, Product } from '../../types/catalog'

export interface OfferWritePayload {
  product_id: string
  price: string
  stock: number
  available: boolean
}

export interface OfferUpdatePayload {
  price?: string
  stock?: number
  available?: boolean
}

export interface ProductWritePayload {
  name: string
  description?: string | null
}

export function fetchProducts(): Promise<Product[]> {
  return apiRequest<Product[]>('/products')
}

export function fetchProduct(productId: string): Promise<Product> {
  return apiRequest<Product>(`/products/${productId}`)
}

export function createProduct(payload: ProductWritePayload): Promise<Product> {
  return apiRequest<Product>('/products', { method: 'POST', body: payload })
}

export function updateProduct(productId: string, payload: ProductWritePayload): Promise<Product> {
  return apiRequest<Product>(`/products/${productId}`, { method: 'PATCH', body: payload })
}

export function deleteProduct(productId: string): Promise<void> {
  return apiRequest(`/products/${productId}`, { method: 'DELETE' })
}

export function fetchOffers(sellerId?: string): Promise<Offer[]> {
  const query = sellerId ? `?seller_id=${encodeURIComponent(sellerId)}` : ''
  return apiRequest<Offer[]>(`/offers${query}`)
}

export function fetchOffer(offerId: string): Promise<Offer> {
  return apiRequest<Offer>(`/offers/${offerId}`)
}

export function createOffer(payload: OfferWritePayload): Promise<Offer> {
  return apiRequest<Offer>('/offers', { method: 'POST', body: payload })
}

export function updateOffer(offerId: string, payload: OfferUpdatePayload): Promise<Offer> {
  return apiRequest<Offer>(`/offers/${offerId}`, { method: 'PATCH', body: payload })
}

export function deleteOffer(offerId: string): Promise<void> {
  return apiRequest(`/offers/${offerId}`, { method: 'DELETE' })
}
