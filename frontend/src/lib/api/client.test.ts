import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { getToken, setToken, clearToken } from '../auth/storage'
import { apiRequest, ApiRequestError, setUnauthorizedHandler } from './client'

function jsonResponse(status: number, body: unknown) {
  return Promise.resolve(
    new Response(JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    }),
  )
}

describe('apiRequest', () => {
  beforeEach(() => {
    clearToken()
    setUnauthorizedHandler(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('sends the bearer token when a session exists', async () => {
    setToken('token-123')
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockImplementation(() => jsonResponse(200, { ok: true }))

    await apiRequest('/whoami')

    const [, init] = fetchMock.mock.calls[0]
    const headers = init!.headers as Record<string, string>
    expect(headers.Authorization).toBe('Bearer token-123')
  })

  it('normalizes a domain error body', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() =>
      jsonResponse(404, { code: 'resource_not_found', message: 'Order item not found' }),
    )

    await expect(apiRequest('/order-items/x')).rejects.toMatchObject({
      code: 'resource_not_found',
      status: 404,
    })
  })

  it('normalizes a 422 validation error body', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() =>
      jsonResponse(422, { detail: [{ msg: 'field required', loc: ['body', 'email'] }] }),
    )

    try {
      await apiRequest('/auth/login', { method: 'POST', body: {}, auth: false })
      throw new Error('expected apiRequest to reject')
    } catch (err) {
      expect(err).toBeInstanceOf(ApiRequestError)
      expect((err as ApiRequestError).code).toBe('validation_error')
      expect((err as ApiRequestError).message).toContain('field required')
    }
  })

  it('clears the token and notifies on 401', async () => {
    setToken('token-123')
    const handler = vi.fn()
    setUnauthorizedHandler(handler)
    vi.spyOn(globalThis, 'fetch').mockImplementation(() =>
      jsonResponse(401, { code: 'unauthorized', message: 'Invalid credentials' }),
    )

    await expect(apiRequest('/auth/me')).rejects.toBeInstanceOf(ApiRequestError)
    expect(handler).toHaveBeenCalledOnce()
    expect(getToken()).toBeNull()
  })
})
