import { Box } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { Page } from '../../components/layout/Page'
import { PageHeader } from '../../components/layout/PageHeader'
import { formatCurrencyBRL } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import { useAuth } from '../../app/providers/auth-context'
import type { Offer } from '../../types/catalog'
import type { Order } from '../../types/order'
import { fetchOffers, fetchProduct } from './api'
import { PurchasePanel } from './PurchasePanel'
import styles from './ProductDetailPage.module.css'

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
    <Page>
      <PageHeader
        title={product.name}
        breadcrumbs={[{ label: 'Catálogo', to: '/catalog' }, { label: product.name }]}
      />

      <div className={styles.layout}>
        <Card>
          <div className={styles.summary}>
            <div className={styles.gallery}>
              <Box size={48} aria-hidden="true" />
            </div>
            {product.description && <p className={styles.description}>{product.description}</p>}
          </div>
        </Card>

        <div className={styles.buyBox}>
          <Card>
            <h2>Ofertas</h2>
            {isBuyer ? (
              <PurchasePanel offers={offers} onPurchased={handlePurchased} />
            ) : (
              <ReadOnlyOffers offers={offers} />
            )}
          </Card>
        </div>
      </div>
    </Page>
  )
}

function ReadOnlyOffers({ offers }: { offers: Offer[] }) {
  if (offers.length === 0) {
    return <p className="text-muted">Nenhuma oferta cadastrada para este produto.</p>
  }
  return (
    <ul className={styles.offerList}>
      {offers.map((offer) => (
        <li key={offer.id} className={styles.offerRow}>
          <span className={styles.offerSeller}>{offer.seller.name}</span>
          <span className={styles.offerPrice}>{formatCurrencyBRL(offer.price)}</span>
          <span className="text-muted">
            {offer.stock} em estoque · {offer.available ? 'Disponível' : 'Indisponível'}
          </span>
        </li>
      ))}
    </ul>
  )
}
