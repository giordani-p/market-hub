import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AuthContext } from '../../app/providers/auth-context'
import type { AuthUser } from '../../types/auth'
import type { Offer, Product } from '../../types/catalog'
import { ProductDetailPage } from './ProductDetailPage'
import { ProductListPage } from './ProductListPage'

const { fetchProducts, fetchOffers, fetchProduct } = vi.hoisted(() => ({
  fetchProducts: vi.fn(),
  fetchOffers: vi.fn(),
  fetchProduct: vi.fn(),
}))

vi.mock('./api', () => ({ fetchProducts, fetchOffers, fetchProduct }))

const product: Product = { id: 'product-1', name: 'Tenis Runner', description: 'Leve' }
const offer: Offer = {
  id: 'offer-1',
  product_id: 'product-1',
  seller_id: 'seller-1',
  price: '199.90',
  stock: 3,
  available: true,
}

const seller: AuthUser = {
  id: '1',
  email: 'seller@x.test',
  name: 'Loja A',
  role: 'seller',
  seller_id: 'seller-1',
}

describe('catalog pages', () => {
  afterEach(() => {
    fetchProducts.mockReset()
    fetchOffers.mockReset()
    fetchProduct.mockReset()
  })

  it('shows the lowest available price on the product card', async () => {
    fetchProducts.mockResolvedValue([product])
    fetchOffers.mockResolvedValue([offer, { ...offer, id: 'offer-2', price: '150.00' }])

    render(
      <MemoryRouter>
        <ProductListPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Tenis Runner')).toBeInTheDocument()
    expect(screen.getByText(/A partir de/)).toHaveTextContent('R$')
  })

  it('hides the purchase button from a seller', async () => {
    fetchProduct.mockResolvedValue(product)
    fetchOffers.mockResolvedValue([offer])

    render(
      <AuthContext.Provider
        value={{ status: 'authenticated', user: seller, login: vi.fn(), logout: vi.fn() }}
      >
        <MemoryRouter initialEntries={['/catalog/product-1']}>
          <Routes>
            <Route path="/catalog/:productId" element={<ProductDetailPage />} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>,
    )

    expect(await screen.findByText('Ofertas')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Comprar' })).not.toBeInTheDocument()
  })
})
