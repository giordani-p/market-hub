import { apiRequest } from '../../lib/api/client'
import type { Offer, Product } from '../../types/catalog'

export function fetchProducts(): Promise<Product[]> {
  return apiRequest<Product[]>('/products')
}

export function fetchProduct(productId: string): Promise<Product> {
  return apiRequest<Product>(`/products/${productId}`)
}

export function fetchOffers(): Promise<Offer[]> {
  return apiRequest<Offer[]>('/offers')
}
