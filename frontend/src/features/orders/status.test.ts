import { describe, expect, it } from 'vitest'
import { canBuyerCancel } from './status'

describe('canBuyerCancel', () => {
  it('allows placed and preparing only', () => {
    expect(canBuyerCancel('placed')).toBe(true)
    expect(canBuyerCancel('preparing')).toBe(true)
    expect(canBuyerCancel('in_transit')).toBe(false)
    expect(canBuyerCancel('delivered')).toBe(false)
    expect(canBuyerCancel('cancelled')).toBe(false)
  })
})
