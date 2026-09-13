import { apiRequest } from '../../lib/api/client'
import type { AuthUser, LoginRequest, TokenResponse } from '../../types/auth'

export function login(payload: LoginRequest): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/auth/login', { method: 'POST', body: payload, auth: false })
}

export function fetchCurrentUser(): Promise<AuthUser> {
  return apiRequest<AuthUser>('/auth/me')
}
