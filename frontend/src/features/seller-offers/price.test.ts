import { describe, expect, it } from 'vitest'
import { toApiPrice } from './price'

describe('toApiPrice', () => {
  it('formats comma and integer input as two decimal places', () => {
    expect(toApiPrice('10')).toBe('10.00')
    expect(toApiPrice('10,5')).toBe('10.50')
    expect(toApiPrice(' 19.9 ')).toBe('19.90')
  })

  it('rejects empty or negative values', () => {
    expect(toApiPrice('')).toBeNull()
    expect(toApiPrice('-1')).toBeNull()
    expect(toApiPrice('abc')).toBeNull()
  })
})
