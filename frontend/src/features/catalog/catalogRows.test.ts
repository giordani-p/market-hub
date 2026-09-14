import { describe, expect, it } from 'vitest'
import type { Offer, Product } from '../../types/catalog'
import { deriveCatalogRows } from './catalogRows'

function product(id: string, name = `Produto ${id}`): Product {
  return { id, name, description: null }
}

function offer(overrides: Partial<Offer> & { id: string; product_id: string }): Offer {
  return {
    seller_id: 'seller-1',
    price: '100.00',
    stock: 5,
    available: true,
    ...overrides,
  }
}

describe('deriveCatalogRows', () => {
  it('marks a product without any offer as out of stock', () => {
    const [row] = deriveCatalogRows([product('p1')], [])

    expect(row.inStock).toBe(false)
    expect(row.lowestPrice).toBeNull()
    expect(row.highestPrice).toBeNull()
    expect(row.sellerCount).toBe(0)
    expect(row.offerCount).toBe(0)
  })

  it('ignores offers that are unavailable or out of stock', () => {
    const [row] = deriveCatalogRows(
      [product('p1')],
      [
        offer({ id: 'o1', product_id: 'p1', available: false, price: '10.00' }),
        offer({ id: 'o2', product_id: 'p1', stock: 0, price: '20.00' }),
      ],
    )

    expect(row.inStock).toBe(false)
    expect(row.lowestPrice).toBeNull()
  })

  it('takes the lowest and the highest purchasable price', () => {
    const [row] = deriveCatalogRows(
      [product('p1')],
      [
        offer({ id: 'o1', product_id: 'p1', price: '199.90' }),
        offer({ id: 'o2', product_id: 'p1', price: '89.90' }),
        offer({ id: 'o3', product_id: 'p1', price: '150.00' }),
        // Fora da conta: indisponivel, mesmo sendo a mais barata.
        offer({ id: 'o4', product_id: 'p1', price: '10.00', available: false }),
      ],
    )

    expect(row.lowestPrice).toBe('89.90')
    expect(row.highestPrice).toBe('199.90')
    expect(row.offerCount).toBe(3)
  })

  it('counts distinct sellers, not offers', () => {
    const [row] = deriveCatalogRows(
      [product('p1')],
      [
        offer({ id: 'o1', product_id: 'p1', seller_id: 'seller-1' }),
        offer({ id: 'o2', product_id: 'p1', seller_id: 'seller-1', price: '90.00' }),
        offer({ id: 'o3', product_id: 'p1', seller_id: 'seller-2' }),
      ],
    )

    expect(row.offerCount).toBe(3)
    expect(row.sellerCount).toBe(2)
  })

  it('keeps the order of the products it received', () => {
    const rows = deriveCatalogRows([product('p1'), product('p2'), product('p3')], [])

    expect(rows.map((row) => row.product.id)).toEqual(['p1', 'p2', 'p3'])
  })

  it('does not leak offers from one product into another', () => {
    const rows = deriveCatalogRows(
      [product('p1'), product('p2')],
      [offer({ id: 'o1', product_id: 'p2', price: '42.00' })],
    )

    expect(rows[0].inStock).toBe(false)
    expect(rows[1].lowestPrice).toBe('42.00')
  })
})
