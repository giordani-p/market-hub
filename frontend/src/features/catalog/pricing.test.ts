import { describe, expect, it } from 'vitest'
import type { Offer } from '../../types/catalog'
import { lowestAvailablePrice } from './pricing'

const offers: Offer[] = [
  {
    id: 'a',
    product_id: 'p',
    seller_id: 's',
    price: '30.00',
    stock: 2,
    available: true,
  },
  {
    id: 'b',
    product_id: 'p',
    seller_id: 's',
    price: '19.90',
    stock: 1,
    available: true,
  },
  {
    id: 'c',
    product_id: 'p',
    seller_id: 's',
    price: '5.00',
    stock: 0,
    available: true,
  },
]

describe('lowestAvailablePrice', () => {
  it('returns the lowest price among available offers with stock', () => {
    expect(lowestAvailablePrice(offers)).toBe('19.90')
  })

  it('returns null when nothing is buyable', () => {
    expect(lowestAvailablePrice(offers.map((offer) => ({ ...offer, stock: 0 })))).toBeNull()
  })
})
