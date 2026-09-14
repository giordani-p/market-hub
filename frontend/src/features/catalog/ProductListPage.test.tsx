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

function renderList(entry = '/catalog') {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <ProductListPage />
    </MemoryRouter>,
  )
}

describe('catalog pages', () => {
  afterEach(() => {
    fetchProducts.mockReset()
    fetchOffers.mockReset()
    fetchProduct.mockReset()
  })

  it('shows the lowest available price and how many stores carry the product', async () => {
    fetchProducts.mockResolvedValue([product])
    fetchOffers.mockResolvedValue([
      offer,
      { ...offer, id: 'offer-2', seller_id: 'seller-2', price: '150.00' },
    ])

    renderList()

    expect(await screen.findByText('Tenis Runner')).toBeInTheDocument()
    expect(screen.getByText('R$ 150,00')).toBeInTheDocument()
    expect(screen.getByText('em 2 lojas')).toBeInTheDocument()
  })

  it('marks a product with no purchasable offer as out of stock', async () => {
    fetchProducts.mockResolvedValue([product])
    fetchOffers.mockResolvedValue([{ ...offer, stock: 0 }])

    renderList()

    expect(await screen.findByText('Sem estoque')).toBeInTheDocument()
    expect(screen.queryByText(/A partir de/)).not.toBeInTheDocument()
  })

  it('announces how many results are on screen', async () => {
    fetchProducts.mockResolvedValue([product, { ...product, id: 'product-2', name: 'Boné' }])
    fetchOffers.mockResolvedValue([offer])

    renderList()

    const count = await screen.findByRole('status')
    expect(count).toHaveTextContent('2 produtos')
    expect(count).toHaveAttribute('aria-live', 'polite')
  })

  it('initializes search and sort from the query string', async () => {
    fetchProducts.mockResolvedValue([
      { ...product, id: 'product-1', name: 'Cafeteira elétrica' },
      { ...product, id: 'product-2', name: 'Bola de futebol' },
    ])
    fetchOffers.mockResolvedValue([
      { ...offer, id: 'o1', product_id: 'product-1', price: '429.00' },
      { ...offer, id: 'o2', product_id: 'product-2', price: '89.00' },
    ])

    renderList('/catalog?q=cafeteira')

    expect(await screen.findByText('Cafeteira elétrica')).toBeInTheDocument()
    expect(screen.queryByText('Bola de futebol')).not.toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('1 produto')
  })

  it('orders by price when the query string asks for it', async () => {
    fetchProducts.mockResolvedValue([
      { ...product, id: 'product-1', name: 'Cafeteira' },
      { ...product, id: 'product-2', name: 'Bola' },
    ])
    fetchOffers.mockResolvedValue([
      { ...offer, id: 'o1', product_id: 'product-1', price: '429.00' },
      { ...offer, id: 'o2', product_id: 'product-2', price: '89.00' },
    ])

    renderList('/catalog?sort=price_asc')

    const names = (await screen.findAllByRole('heading', { level: 3 })).map(
      (heading) => heading.textContent,
    )
    expect(names).toEqual(['Bola', 'Cafeteira'])
  })

  it('separates an empty catalog from a filter with no match', async () => {
    fetchProducts.mockResolvedValue([])
    fetchOffers.mockResolvedValue([])

    const { unmount } = renderList()
    expect(await screen.findByText('Nenhum produto no catálogo ainda.')).toBeInTheDocument()
    unmount()

    fetchProducts.mockResolvedValue([product])
    fetchOffers.mockResolvedValue([offer])

    renderList('/catalog?q=inexistente')
    expect(await screen.findByText('Nenhum produto corresponde aos filtros.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Limpar filtros' })).toBeInTheDocument()
  })

  it('warns about an inverted price range instead of emptying the list', async () => {
    fetchProducts.mockResolvedValue([product])
    fetchOffers.mockResolvedValue([offer])

    renderList('/catalog?min=500&max=100')

    expect(await screen.findByText('Tenis Runner')).toBeInTheDocument()
    expect(screen.getByText('O mínimo não pode ser maior que o máximo.')).toBeInTheDocument()
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
