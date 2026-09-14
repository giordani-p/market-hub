import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { ReactNode } from 'react'
import { AuthContext } from '../../app/providers/auth-context'
import { ToastProvider } from '../../components/overlay/ToastProvider'
import { ApiRequestError } from '../../lib/api/client'
import type { AuthUser } from '../../types/auth'
import type { Offer, Product } from '../../types/catalog'
import { SellerOfferDetailPage } from './SellerOfferDetailPage'
import { SellerOffersListPage } from './SellerOffersListPage'

const api = vi.hoisted(() => ({
  fetchOffers: vi.fn(),
  fetchProducts: vi.fn(),
  fetchOffer: vi.fn(),
  fetchProduct: vi.fn(),
  deleteOffer: vi.fn(),
  deleteProduct: vi.fn(),
  updateOffer: vi.fn(),
  updateProduct: vi.fn(),
}))

vi.mock('../catalog/api', () => api)

const seller: AuthUser = {
  id: '1',
  email: 'seller@x.test',
  name: 'Loja A',
  role: 'seller',
  seller_id: 'seller-1',
}

const product: Product = { id: 'product-1', name: 'Tenis Runner', description: null }
const offer: Offer = {
  id: 'offer-1',
  product_id: 'product-1',
  seller_id: 'seller-1',
  price: '199.90',
  stock: 3,
  available: true,
}

function authWrap(ui: ReactNode) {
  return (
    <ToastProvider>
      <AuthContext.Provider
        value={{ status: 'authenticated', user: seller, login: vi.fn(), logout: vi.fn() }}
      >
        {ui}
      </AuthContext.Provider>
    </ToastProvider>
  )
}

describe('seller offers', () => {
  afterEach(() => {
    Object.values(api).forEach((fn) => fn.mockReset())
  })

  it('lists offers filtered by the authenticated seller', async () => {
    api.fetchOffers.mockResolvedValue([offer])
    api.fetchProducts.mockResolvedValue([product])

    render(
      authWrap(
        <MemoryRouter>
          <SellerOffersListPage />
        </MemoryRouter>,
      ),
    )

    expect(await screen.findByText('Tenis Runner')).toBeInTheDocument()
    expect(api.fetchOffers).toHaveBeenCalledWith('seller-1')
  })

  it('shows the 409 message when deleting an offer in use', async () => {
    api.fetchOffer.mockResolvedValue(offer)
    api.fetchProduct.mockResolvedValue(product)
    api.deleteOffer.mockRejectedValue(
      new ApiRequestError({
        status: 409,
        code: 'resource_in_use',
        message: 'Offer has associated order items',
      }),
    )

    render(
      authWrap(
        <MemoryRouter initialEntries={['/seller/offers/offer-1']}>
          <Routes>
            <Route path="/seller/offers/:offerId" element={<SellerOfferDetailPage />} />
          </Routes>
        </MemoryRouter>,
      ),
    )

    expect(await screen.findByRole('button', { name: 'Excluir oferta' })).toBeInTheDocument()
    const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: 'Excluir oferta' }))
    await user.click(screen.getByRole('button', { name: 'Confirmar exclusão' }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Offer has associated order items')
    })
  })
})
