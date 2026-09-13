export type UserRole = 'buyer' | 'seller' | 'ops'

export interface AuthUser {
  id: string
  email: string
  name: string
  role: UserRole
  seller_id: string | null
}

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}
