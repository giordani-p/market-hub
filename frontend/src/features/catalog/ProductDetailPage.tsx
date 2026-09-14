import { useNavigate, useParams } from 'react-router-dom'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { formatCurrencyBRL } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import { useAuth } from '../../app/providers/auth-context'
import type { Order } from '../../types/order'
import { fetchOffers, fetchProduct } from './api'
import { PurchasePanel } from './PurchasePanel'

export function ProductDetailPage() {
  const { productId } = useParams<{ productId: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()

  const state = useAsync(async () => {
    const [product, offers] = await Promise.all([fetchProduct(productId!), fetchOffers()])
    return { product, offers: offers.filter((offer) => offer.product_id === productId) }
  }, [productId])

  if (state.status === 'loading') {
    return <Spinner label="Carregando produto..." />
  }
  if (state.status === 'error') {
    return <ErrorState message={state.error} onRetry={state.retry} />
  }

  const { product, offers } = state.data
  const isBuyer = user?.role === 'buyer'

  function handlePurchased(order: Order) {
    navigate(`/buyer/orders/${order.id}`)
  }

  return (
    <div className="page">
      <h1>{product.name}</h1>
      {product.description && <p className="text-muted">{product.description}</p>}

      <section className="dashboard-section">
        <h2>Ofertas</h2>
        {offers.length === 0 ? (
          <p className="text-muted">Nenhuma oferta cadastrada para este produto.</p>
        ) : (
          <ul className="offer-list">
            {offers.map((offer) => (
              <li key={offer.id} className="offer-option offer-option-readonly">
                <span>{formatCurrencyBRL(offer.price)}</span>
                <span className="text-muted">{offer.stock} em estoque</span>
                <span className="text-muted">{offer.available ? 'Disponível' : 'Indisponível'}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {isBuyer && <PurchasePanel offers={offers} onPurchased={handlePurchased} />}
    </div>
  )
}
