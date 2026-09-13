import { clearToken, getToken } from '../auth/storage'
import { normalizeErrorBody, type ApiError } from './errors'

const DEFAULT_BASE_URL = 'http://localhost:8000/v1'

function baseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? DEFAULT_BASE_URL
}

export class ApiRequestError extends Error {
  status: number
  code: string

  constructor(error: ApiError) {
    super(error.message)
    this.status = error.status
    this.code = error.code
  }
}

type UnauthorizedHandler = () => void

let onUnauthorized: UnauthorizedHandler | null = null

/** Registrado pelo AuthProvider para deslogar em qualquer 401 vindo da API. */
export function setUnauthorizedHandler(handler: UnauthorizedHandler): void {
  onUnauthorized = handler
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: unknown
  /** false para chamadas que não devem enviar o Bearer token (ex.: login). */
  auth?: boolean
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, auth = true } = options

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (auth) {
    const token = getToken()
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
  }

  const response = await fetch(`${baseUrl()}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (response.status === 204) {
    return undefined as T
  }

  const data: unknown = await response.json().catch(() => undefined)

  if (!response.ok) {
    const error = normalizeErrorBody(response.status, data)
    if (response.status === 401) {
      clearToken()
      onUnauthorized?.()
    }
    throw new ApiRequestError(error)
  }

  return data as T
}
