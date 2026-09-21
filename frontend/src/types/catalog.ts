export interface Product {
  id: string
  name: string
  description: string | null
}

export interface SellerSummary {
  id: string
  name: string
}

export interface Offer {
  id: string
  product_id: string
  seller_id: string
  seller: SellerSummary
  price: string
  stock: number
  available: boolean
}
