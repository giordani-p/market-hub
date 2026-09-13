import { describe, expect, it } from 'vitest'
import { normalizeErrorBody } from './errors'

describe('normalizeErrorBody', () => {
  it('normalizes a plain domain error without extra fields', () => {
    const result = normalizeErrorBody(404, { code: 'resource_not_found', message: 'Not found' })
    expect(result).toEqual({
      status: 404,
      code: 'resource_not_found',
      message: 'Not found',
      details: { code: 'resource_not_found', message: 'Not found' },
    })
  })

  it('keeps the checkout_rejected items in details', () => {
    const body = {
      code: 'checkout_rejected',
      message: 'One or more items require review',
      items: [
        {
          offer_id: 'offer-1',
          reason: 'insufficient_stock',
          expected_price: '10.00',
          current_price: '10.00',
          available: true,
          stock: 0,
        },
      ],
    }

    const result = normalizeErrorBody(409, body)

    expect(result.code).toBe('checkout_rejected')
    expect(result.details).toEqual(body)
  })

  it('normalizes a 422 validation error', () => {
    const result = normalizeErrorBody(422, {
      detail: [{ msg: 'field required', loc: ['body', 'email'] }],
    })
    expect(result).toEqual({ status: 422, code: 'validation_error', message: 'field required' })
  })
})
