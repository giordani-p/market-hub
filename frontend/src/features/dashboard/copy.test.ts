import { describe, expect, it } from 'vitest'
import { BUYER_ORDER_STATUS_LABELS } from './copy'

describe('BUYER_ORDER_STATUS_LABELS', () => {
  it('maps the three projection statuses to Portuguese labels', () => {
    expect(BUYER_ORDER_STATUS_LABELS.in_progress).toBe('Em andamento')
    expect(BUYER_ORDER_STATUS_LABELS.completed).toBe('Concluído')
    expect(BUYER_ORDER_STATUS_LABELS.cancelled).toBe('Cancelado')
  })
})
