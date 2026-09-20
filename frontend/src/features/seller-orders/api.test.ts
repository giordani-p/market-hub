import { describe, expect, it } from 'vitest'
import { buildSellerOrderItemsQuery } from './api'

describe('buildSellerOrderItemsQuery', () => {
  it('returns an empty string with no filters', () => {
    expect(buildSellerOrderItemsQuery({})).toBe('')
  })

  it('includes only the filters that are present', () => {
    const query = buildSellerOrderItemsQuery({ page: 2, status: 'delivered' })
    const params = new URLSearchParams(query.slice(1))
    expect(params.get('page')).toBe('2')
    expect(params.get('status')).toBe('delivered')
    expect(params.has('order_item_id')).toBe(false)
    expect(params.has('from')).toBe(false)
    expect(params.has('to')).toBe(false)
  })

  it('maps orderItemId, from and to to the API param names', () => {
    const query = buildSellerOrderItemsQuery({
      orderItemId: 'item-1',
      from: '2026-01-01T00:00:00Z',
      to: '2026-01-31T23:59:59Z',
    })
    const params = new URLSearchParams(query.slice(1))
    expect(params.get('order_item_id')).toBe('item-1')
    expect(params.get('from')).toBe('2026-01-01T00:00:00Z')
    expect(params.get('to')).toBe('2026-01-31T23:59:59Z')
  })

  it('maps the public number filter', () => {
    const query = buildSellerOrderItemsQuery({ number: '1042-1' })
    const params = new URLSearchParams(query.slice(1))
    expect(params.get('number')).toBe('1042-1')
    expect(params.has('order_item_id')).toBe(false)
  })
})
