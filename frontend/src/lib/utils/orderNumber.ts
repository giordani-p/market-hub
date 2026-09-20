import { isCompleteUuid } from './useUrlFilters'

const PUBLIC_NUMBER_PATTERN = /^\d+(-\d+)?$/

export function formatOrderNumber(number: number): string {
  return `#${number}`
}

export function formatOrderItemNumber(number: string): string {
  return `#${number}`
}

export function isPublicNumber(value: string): boolean {
  return PUBLIC_NUMBER_PATTERN.test(value.trim())
}

export type OrderLookupStatus = 'empty' | 'uuid' | 'number' | 'invalid'

export interface OrderLookup {
  status: OrderLookupStatus
  value: string
}

export function classifyOrderLookup(raw: string): OrderLookup {
  const value = raw.trim()
  if (!value) {
    return { status: 'empty', value: '' }
  }
  if (isCompleteUuid(value)) {
    return { status: 'uuid', value }
  }
  if (isPublicNumber(value)) {
    return { status: 'number', value }
  }
  return { status: 'invalid', value }
}

export interface OrderLookupParams {
  number: string | null
  orderItemId: string | null
}

export function nextLookupParams(raw: string): OrderLookupParams {
  const classified = classifyOrderLookup(raw)
  if (classified.status === 'empty') {
    return { number: null, orderItemId: null }
  }
  if (classified.status === 'uuid') {
    return { number: null, orderItemId: classified.value }
  }
  if (classified.status === 'number') {
    return { number: classified.value, orderItemId: null }
  }
  if (/^\d/.test(classified.value)) {
    return { number: classified.value, orderItemId: null }
  }
  return { number: null, orderItemId: classified.value }
}

export const ORDER_LOOKUP_ERROR = 'Informe o número do pedido (1042 ou 1042-1).'
export const ORDER_LOOKUP_HINT = 'Número do pedido, como 1042 ou 1042-1.'

export function orderLookupChipLabel(raw: string): string {
  const lookup = classifyOrderLookup(raw)
  if (lookup.status === 'number') {
    return lookup.value.includes('-')
      ? `Pedido ${formatOrderItemNumber(lookup.value)}`
      : `Pedido ${formatOrderNumber(Number(lookup.value))}`
  }
  if (lookup.status === 'uuid') {
    return 'Pedido'
  }
  return `Pedido ${raw}`
}

export function applyLookupToFilters(
  set: (key: string, value: string | null) => void,
  raw: string,
): void {
  const next = nextLookupParams(raw)
  set('order_item_id', next.orderItemId)
  set('number', next.number)
}
