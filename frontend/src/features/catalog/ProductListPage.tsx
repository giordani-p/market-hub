import { Box } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Checkbox } from '../../components/ui/Checkbox'
import { TextField } from '../../components/ui/TextField'
import { FilterBar, type ActiveFilter } from '../../components/data/FilterBar'
import filterStyles from '../../components/data/FilterBar.module.css'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { SkeletonList } from '../../components/ui/Skeleton'
import { Page } from '../../components/layout/Page'
import { PageHeader } from '../../components/layout/PageHeader'
import { formatCurrencyBRL } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import { fetchOffers, fetchProducts } from './api'
import { lowestAvailablePrice } from './pricing'
import styles from './ProductListPage.module.css'

export function ProductListPage() {
  const state = useAsync(async () => {
    const [products, offers] = await Promise.all([fetchProducts(), fetchOffers()])
    return { products, offers }
  }, [])

  // Filtros na URL: a busca do header entra por aqui e a tela filtrada
  // vira um link que pode ser compartilhado.
  const [searchParams, setSearchParams] = useSearchParams()
  const search = searchParams.get('q') ?? ''
  const availableOnly = searchParams.get('available') === 'true'

  function updateParam(key: string, value: string | null) {
    setSearchParams(
      (current) => {
        const next = new URLSearchParams(current)
        if (value) {
          next.set(key, value)
        } else {
          next.delete(key)
        }
        return next
      },
      { replace: true },
    )
  }

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

  const activeFilters: ActiveFilter[] = [
    ...(search
      ? [{ key: 'q', label: `Busca: ${search}`, onRemove: () => updateParam('q', null) }]
      : []),
    ...(availableOnly
      ? [
          {
            key: 'available',
            label: 'Somente disponíveis',
            onRemove: () => updateParam('available', null),
          },
        ]
      : []),
  ]

  return (
    <Page>
      <PageHeader title="Catálogo" subtitle="Produtos publicados pelas lojas do Market Hub." />

      <FilterBar
        active={activeFilters}
        onClearAll={() => setSearchParams(new URLSearchParams(), { replace: true })}
      >
        <TextField
          label="Buscar produto"
          name="q"
          type="search"
          value={search}
          onChange={(event) => updateParam('q', event.target.value || null)}
          placeholder="Nome do produto"
        />
        <Checkbox
          label="Somente disponíveis"
          name="available"
          className={filterStyles.alignWithControl}
          checked={availableOnly}
          onChange={(event) => updateParam('available', event.target.checked ? 'true' : null)}
        />
      </FilterBar>

      {state.status === 'loading' && <SkeletonList variant="card" label="Carregando produtos..." />}
      {state.status === 'error' && <ErrorState message={state.error} onRetry={state.retry} />}
      {state.status === 'success' && products.length === 0 && (
        <EmptyState title="Nenhum produto no catálogo ainda." />
      )}
      {state.status === 'success' && products.length > 0 && visible.length === 0 && (
        <EmptyState
          title="Nenhum produto corresponde ao filtro."
          description="Tente outro termo ou remova os filtros aplicados."
          action={
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => setSearchParams(new URLSearchParams(), { replace: true })}
            >
              Limpar filtros
            </Button>
          }
        />
      )}

      {state.status === 'success' && visible.length > 0 && (
        <div className={styles.grid}>
          {visible.map((product) => {
            const price = lowestAvailablePrice(
              offers.filter((offer) => offer.product_id === product.id),
            )
            return (
              <Link key={product.id} to={`/catalog/${product.id}`} className={styles.productLink}>
                <Card interactive>
                  <div className={styles.product}>
                    <div className={styles.thumb}>
                      <Box size={32} aria-hidden="true" />
                    </div>
                    <h2 className={styles.name}>{product.name}</h2>
                    {price ? (
                      <p className={styles.price}>
                        A partir de
                        <span className={styles.priceValue}>{formatCurrencyBRL(price)}</span>
                      </p>
                    ) : (
                      <p className={styles.unavailable}>Sem ofertas disponíveis</p>
                    )}
                  </div>
                </Card>
              </Link>
            )
          })}
        </div>
      )}
    </Page>
  )
}
