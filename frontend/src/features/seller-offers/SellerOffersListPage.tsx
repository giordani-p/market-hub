import { Link } from 'react-router-dom'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { useAuth } from '../../app/providers/auth-context'
import { formatCurrencyBRL } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import { fetchOffers, fetchProducts } from '../catalog/api'

export function SellerOffersListPage() {
  const { user } = useAuth()
  const sellerId = user?.seller_id

  const state = useAsync(async () => {
    if (!sellerId) {
      throw new Error('Seller sem loja associada.')
    }
    const [offers, products] = await Promise.all([fetchOffers(sellerId), fetchProducts()])
    const names = new Map(products.map((product) => [product.id, product.name]))
    return { offers, names }
  }, [sellerId])

  if (state.status === 'loading') {
    return <Spinner label="Carregando ofertas..." />
  }
  if (state.status === 'error') {
    return <ErrorState message={state.error} onRetry={state.retry} />
  }

  const { offers, names } = state.data

  return (
    <div className="page">
      <div className="page-header-row">
        <h1>Minhas ofertas</h1>
        <Link to="/seller/offers/new">
          <Button type="button">Nova oferta</Button>
        </Link>
      </div>

      {offers.length === 0 ? (
        <EmptyState
          title="Você ainda não tem ofertas."
          description="Cadastre um produto da vitrine e publique preço e estoque."
        />
      ) : (
        <div className="order-list">
          {offers.map((offer) => (
            <Link key={offer.id} to={`/seller/offers/${offer.id}`} className="product-link">
              <Card>
                <div className="order-item-row">
                  <span>{names.get(offer.product_id) ?? 'Produto'}</span>
                  <span>{formatCurrencyBRL(offer.price)}</span>
                  <span className="text-muted">{offer.stock} em estoque</span>
                  <span className="text-muted">
                    {offer.available ? 'Disponível' : 'Indisponível'}
                  </span>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
