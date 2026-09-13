import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { useAsync } from '../../lib/utils/useAsync'
import { fetchProducts } from './api'

export function ProductListPage() {
  const state = useAsync(fetchProducts, [])
  const [search, setSearch] = useState('')

  const products = state.status === 'success' ? state.data : []
  const term = search.trim().toLowerCase()
  const filtered = term
    ? products.filter((product) => product.name.toLowerCase().includes(term))
    : products

  return (
    <div className="page">
      <h1>Catálogo</h1>
      <Input
        label="Buscar produto"
        name="search"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        placeholder="Nome do produto"
      />

      {state.status === 'loading' && <Spinner label="Carregando produtos..." />}
      {state.status === 'error' && <ErrorState message={state.error} onRetry={state.retry} />}
      {state.status === 'success' && products.length === 0 && (
        <EmptyState title="Nenhum produto encontrado." />
      )}
      {state.status === 'success' && products.length > 0 && filtered.length === 0 && (
        <EmptyState title="Nenhum produto encontrado para a busca." />
      )}

      {state.status === 'success' && filtered.length > 0 && (
        <div className="product-grid">
          {filtered.map((product) => (
            <Link key={product.id} to={`/buyer/catalog/${product.id}`} className="product-link">
              <Card>
                <h2>{product.name}</h2>
                {product.description && <p className="text-muted">{product.description}</p>}
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
