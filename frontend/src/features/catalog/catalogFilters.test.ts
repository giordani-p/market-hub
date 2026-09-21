import { describe, expect, it } from 'vitest'
import type { CatalogRow } from './catalogRows'
import {
  applyCatalogFilters,
  isPriceRangeInverted,
  normalizeText,
  parsePriceInput,
  type CatalogFilterValues,
} from './catalogFilters'

function row(overrides: Partial<CatalogRow> & { id: string }): CatalogRow {
  const { id, ...rest } = overrides
  return {
    product: { id, name: `Produto ${id}`, description: null },
    lowestPrice: '100.00',
    highestPrice: '100.00',
    sellerCount: 1,
    sellerNames: ['Loja A'],
    offerCount: 1,
    inStock: true,
    ...rest,
  }
}

function values(overrides: Partial<CatalogFilterValues> = {}): CatalogFilterValues {
  return { search: '', minPrice: '', maxPrice: '', availableOnly: false, ...overrides }
}

describe('normalizeText', () => {
  it('drops accent and case', () => {
    expect(normalizeText('Relógio Analógico')).toBe('relogio analogico')
  })
})

describe('parsePriceInput', () => {
  it('accepts comma as the decimal separator', () => {
    expect(parsePriceInput('19,90')).toBe(19.9)
  })

  it('rejects what does not work as a filter', () => {
    expect(parsePriceInput('')).toBeNull()
    expect(parsePriceInput('abc')).toBeNull()
    expect(parsePriceInput('-5')).toBeNull()
  })
})

describe('applyCatalogFilters', () => {
  const rows = [
    row({ id: 'p1', product: { id: 'p1', name: 'Relógio analógico', description: null } }),
    row({
      id: 'p2',
      product: { id: 'p2', name: 'Tênis casual', description: 'Solado de borracha' },
      lowestPrice: '249.00',
    }),
    row({ id: 'p3', lowestPrice: null, highestPrice: null, inStock: false, sellerCount: 0, sellerNames: [] }),
  ]

  it('matches the search without accent, in either direction', () => {
    expect(applyCatalogFilters(rows, values({ search: 'relogio' }))).toHaveLength(1)
    expect(applyCatalogFilters(rows, values({ search: 'RELÓGIO' }))).toHaveLength(1)
  })

  it('also searches the description', () => {
    const found = applyCatalogFilters(rows, values({ search: 'borracha' }))

    expect(found.map((item) => item.product.id)).toEqual(['p2'])
  })

  it('applies an open-ended range', () => {
    const found = applyCatalogFilters(rows, values({ minPrice: '200' }))

    expect(found.map((item) => item.product.id)).toEqual(['p2'])
  })

  it('drops products without a price once a price filter is on', () => {
    const found = applyCatalogFilters(rows, values({ maxPrice: '1000' }))

    expect(found.map((item) => item.product.id)).toEqual(['p1', 'p2'])
  })

  it('ignores an inverted range instead of emptying the list', () => {
    expect(isPriceRangeInverted('500', '100')).toBe(true)
    expect(applyCatalogFilters(rows, values({ minPrice: '500', maxPrice: '100' }))).toHaveLength(3)
  })

  it('ignores a price input that is not a usable number', () => {
    expect(applyCatalogFilters(rows, values({ minPrice: 'abc' }))).toHaveLength(3)
  })

  it('keeps only what can be bought when asked', () => {
    const found = applyCatalogFilters(rows, values({ availableOnly: true }))

    expect(found.map((item) => item.product.id)).toEqual(['p1', 'p2'])
  })
})
