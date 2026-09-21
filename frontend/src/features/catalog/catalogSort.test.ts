import { describe, expect, it } from 'vitest'
import type { CatalogRow } from './catalogRows'
import { parseCatalogSort, sortCatalogRows } from './catalogSort'

function row(id: string, name: string, lowestPrice: string | null): CatalogRow {
  return {
    product: { id, name, description: null },
    lowestPrice,
    highestPrice: lowestPrice,
    sellerCount: lowestPrice ? 1 : 0,
    sellerNames: lowestPrice ? ['Loja A'] : [],
    offerCount: lowestPrice ? 1 : 0,
    inStock: lowestPrice !== null,
  }
}

const rows = [
  row('p1', 'Cafeteira', '429.00'),
  row('p2', 'Bola', '89.00'),
  row('p3', 'Aspirador', null),
  row('p4', 'Ventilador', '150.00'),
]

describe('parseCatalogSort', () => {
  it('falls back to relevance for anything unknown', () => {
    expect(parseCatalogSort('')).toBe('relevance')
    expect(parseCatalogSort('whatever')).toBe('relevance')
    expect(parseCatalogSort('price_desc')).toBe('price_desc')
  })
})

describe('sortCatalogRows', () => {
  it('keeps the API order under relevance', () => {
    expect(sortCatalogRows(rows, 'relevance').map((item) => item.product.id)).toEqual([
      'p1',
      'p2',
      'p3',
      'p4',
    ])
  })

  it('sorts by ascending price and pushes what has no price to the end', () => {
    expect(sortCatalogRows(rows, 'price_asc').map((item) => item.product.id)).toEqual([
      'p2',
      'p4',
      'p1',
      'p3',
    ])
  })

  it('sorts by descending price and still keeps what has no price last', () => {
    expect(sortCatalogRows(rows, 'price_desc').map((item) => item.product.id)).toEqual([
      'p1',
      'p4',
      'p2',
      'p3',
    ])
  })

  it('sorts by name in pt-BR', () => {
    expect(sortCatalogRows(rows, 'name_asc').map((item) => item.product.name)).toEqual([
      'Aspirador',
      'Bola',
      'Cafeteira',
      'Ventilador',
    ])
  })

  it('does not mutate the array it received', () => {
    const original = [...rows]
    sortCatalogRows(rows, 'price_asc')

    expect(rows).toEqual(original)
  })
})
