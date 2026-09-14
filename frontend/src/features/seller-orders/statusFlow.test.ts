import { describe, expect, it } from 'vitest'
import { canCancel, nextStatus } from './statusFlow'

describe('nextStatus', () => {
  it('returns the following step for each forward status', () => {
    expect(nextStatus('placed')).toBe('preparing')
    expect(nextStatus('preparing')).toBe('in_transit')
    expect(nextStatus('in_transit')).toBe('delivered')
  })

  it('returns null for terminal statuses', () => {
    expect(nextStatus('delivered')).toBeNull()
    expect(nextStatus('cancelled')).toBeNull()
  })
})

describe('canCancel', () => {
  it('allows cancelling before delivery', () => {
    expect(canCancel('placed')).toBe(true)
    expect(canCancel('preparing')).toBe(true)
    expect(canCancel('in_transit')).toBe(true)
  })

  it('blocks cancelling once delivered or already cancelled', () => {
    expect(canCancel('delivered')).toBe(false)
    expect(canCancel('cancelled')).toBe(false)
  })
})
