import { useNavigate, useParams } from 'react-router-dom'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { useAsync } from '../../lib/utils/useAsync'
import type { Order } from '../../types/order'
import { fetchOffers, fetchProduct } from './api'
import { PurchasePanel } from './PurchasePanel'

export function ProductDetailPage() {
  const { productId } = useParams<{ productId: string }>()
  const navigate = useNavigate()

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

  function handlePurchased(order: Order) {
    navigate(`/buyer/orders/${order.id}`)
  }

  return (
    <div className="page">
      <h1>{product.name}</h1>
      {product.description && <p className="text-muted">{product.description}</p>}
      <PurchasePanel offers={offers} onPurchased={handlePurchased} />
    </div>
  )
}
