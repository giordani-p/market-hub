import { describe, expect, it } from 'vitest'
import {
  classifyOrderLookup,
  formatOrderItemNumber,
  formatOrderNumber,
  isPublicNumber,
  nextLookupParams,
  orderLookupChipLabel,
} from './orderNumber'

describe('orderNumber', () => {
  it('formats public identifiers with a hash', () => {
    expect(formatOrderNumber(1042)).toBe('#1042')
    expect(formatOrderItemNumber('1042-1')).toBe('#1042-1')
  })

  it('classifies uuid, public number and invalid input', () => {
    expect(classifyOrderLookup('')).toEqual({ status: 'empty', value: '' })
    expect(classifyOrderLookup('1042')).toEqual({ status: 'number', value: '1042' })
    expect(classifyOrderLookup('1042-1')).toEqual({ status: 'number', value: '1042-1' })
    expect(classifyOrderLookup('01000003-0000-4000-8000-000000000001').status).toBe('uuid')
    expect(classifyOrderLookup('1042-').status).toBe('invalid')
    expect(classifyOrderLookup('abc').status).toBe('invalid')
  })

  it('maps the typed value to a single query param', () => {
    expect(nextLookupParams('1042')).toEqual({ number: '1042', orderItemId: null })
    expect(nextLookupParams('01000003-0000-4000-8000-000000000001')).toEqual({
      number: null,
      orderItemId: '01000003-0000-4000-8000-000000000001',
    })
    expect(nextLookupParams('1042-')).toEqual({ number: '1042-', orderItemId: null })
    expect(isPublicNumber('1042-1')).toBe(true)
    expect(isPublicNumber('1042-')).toBe(false)
  })

  it('labels the filter chip without exposing a uuid', () => {
    expect(orderLookupChipLabel('1042')).toBe('Pedido #1042')
    expect(orderLookupChipLabel('1042-1')).toBe('Pedido #1042-1')
    expect(orderLookupChipLabel('01000003-0000-4000-8000-000000000001')).toBe('Pedido')
    expect(orderLookupChipLabel('1042-')).toBe('Pedido 1042-')
  })
})
