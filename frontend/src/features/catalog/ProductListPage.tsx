import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { formatCurrencyBRL } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import { fetchOffers, fetchProducts } from './api'
import { lowestAvailablePrice } from './pricing'

export function ProductListPage() {
  const state = useAsync(async () => {
    const [products, offers] = await Promise.all([fetchProducts(), fetchOffers()])
    return { products, offers }
  }, [])
  const [search, setSearch] = useState('')
  const [availableOnly, setAvailableOnly] = useState(false)

  const products = state.status === 'success' ? state.data.products : []
  const offers = state.status === 'success' ? state.data.offers : []
  const term = search.trim().toLowerCase()

  const visible = products.filter((product) => {
    const matchesSearch = term ? product.name.toLowerCase().includes(term) : true
    if (!matchesSearch) {
      return false
    }
    if (!availableOnly) {
      return true
    }
    return lowestAvailablePrice(offers.filter((offer) => offer.product_id === product.id)) !== null
  })

  return (
    <div className="page">
      <h1>Catálogo</h1>
      <div className="filters">
        <Input
          label="Buscar produto"
          name="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Nome do produto"
        />
        <label className="field checkbox-field">
          <input
            type="checkbox"
            name="availableOnly"
            checked={availableOnly}
            onChange={(event) => setAvailableOnly(event.target.checked)}
          />
          Somente disponíveis
        </label>
      </div>

      {state.status === 'loading' && <Spinner label="Carregando produtos..." />}
      {state.status === 'error' && <ErrorState message={state.error} onRetry={state.retry} />}
      {state.status === 'success' && products.length === 0 && (
        <EmptyState title="Nenhum produto encontrado." />
      )}
      {state.status === 'success' && products.length > 0 && visible.length === 0 && (
        <EmptyState title="Nenhum produto encontrado para a busca." />
      )}

      {state.status === 'success' && visible.length > 0 && (
        <div className="product-grid">
          {visible.map((product) => {
            const price = lowestAvailablePrice(
              offers.filter((offer) => offer.product_id === product.id),
            )
            return (
              <Link key={product.id} to={`/catalog/${product.id}`} className="product-link">
                <Card>
                  <h2>{product.name}</h2>
                  {product.description && <p className="text-muted">{product.description}</p>}
                  {price ? (
                    <p className="product-price">A partir de {formatCurrencyBRL(price)}</p>
                  ) : (
                    <p className="text-muted">Sem ofertas disponíveis</p>
                  )}
                </Card>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
