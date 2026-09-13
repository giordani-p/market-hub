export interface Product {
  id: string
  name: string
  description: string | null
}

export interface Offer {
  id: string
  product_id: string
  seller_id: string
  price: string
  stock: number
  available: boolean
}
