import { useMemo } from 'react'
import { Button } from '../../components/ui/Button'
import { Checkbox } from '../../components/ui/Checkbox'
import { Pagination } from '../../components/ui/Pagination'
import { SelectField } from '../../components/ui/SelectField'
import { Skeleton } from '../../components/ui/Skeleton'
import { TextField } from '../../components/ui/TextField'
import { FilterBar, type ActiveFilter } from '../../components/data/FilterBar'
import filterStyles from '../../components/data/FilterBar.module.css'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Page } from '../../components/layout/Page'
import { PageHeader } from '../../components/layout/PageHeader'
import { useAsync } from '../../lib/utils/useAsync'
import { useDebouncedValue } from '../../lib/utils/useDebouncedValue'
import { useUrlFilters } from '../../lib/utils/useUrlFilters'
import { fetchOffers, fetchProducts } from './api'
import { applyCatalogFilters, isPriceRangeInverted } from './catalogFilters'
import { deriveCatalogRows } from './catalogRows'
import { CATALOG_SORT_OPTIONS, parseCatalogSort, sortCatalogRows } from './catalogSort'
import { ProductCard } from './ProductCard'
import styles from './ProductListPage.module.css'

const PAGE_SIZE = 24

const FILTER_KEYS = ['q', 'min', 'max', 'available']

function countLabel(total: number): string {
  if (total === 0) {
    return 'Nenhum produto'
  }
  return total === 1 ? '1 produto' : `${total} produtos`
}

export function ProductListPage() {
  const state = useAsync(async () => {
    const [products, offers] = await Promise.all([fetchProducts(), fetchOffers()])
    return { products, offers }
  }, [])

  const filters = useUrlFilters()
  const search = filters.get('q')
  const minPrice = filters.get('min')
  const maxPrice = filters.get('max')
  const availableOnly = filters.get('available') === 'true'
  const sort = parseCatalogSort(filters.get('sort'))
  const page = Number(filters.get('page')) || 1

  // O campo responde na hora; o filtro so aplica depois da pausa.
  const debouncedSearch = useDebouncedValue(search)
  const debouncedMin = useDebouncedValue(minPrice)
  const debouncedMax = useDebouncedValue(maxPrice)

  // Erro de faixa sai do valor digitado, nao do debounced: a pessoa precisa
  // do aviso enquanto ainda esta no campo.
  const rangeInverted = isPriceRangeInverted(minPrice, maxPrice)

  const rows = useMemo(
    () =>
      state.status === 'success' ? deriveCatalogRows(state.data.products, state.data.offers) : [],
    [state],
  )

  const visible = useMemo(() => {
    const filtered = applyCatalogFilters(rows, {
      search: debouncedSearch,
      minPrice: debouncedMin,
      maxPrice: debouncedMax,
      availableOnly,
    })
    return sortCatalogRows(filtered, sort)
  }, [rows, debouncedSearch, debouncedMin, debouncedMax, availableOnly, sort])

  const total = visible.length
  const pageRows = visible.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
  const hasFilters = filters.countActive(FILTER_KEYS) > 0

  const activeFilters: ActiveFilter[] = [
    ...(search
      ? [{ key: 'q', label: `Busca: ${search}`, onRemove: () => filters.set('q', null) }]
      : []),
    ...(minPrice
      ? [
          {
            key: 'min',
            label: `A partir de R$ ${minPrice}`,
            onRemove: () => filters.set('min', null),
          },
        ]
      : []),
    ...(maxPrice
      ? [{ key: 'max', label: `Até R$ ${maxPrice}`, onRemove: () => filters.set('max', null) }]
      : []),
    ...(availableOnly
      ? [
          {
            key: 'available',
            label: 'Somente disponíveis',
            onRemove: () => filters.set('available', null),
          },
        ]
      : []),
  ]

  const filterRail = (
    <FilterBar active={activeFilters} onClearAll={filters.clearAll}>
      <TextField
        label="Buscar produto"
        name="q"
        type="search"
        value={search}
        onChange={(event) => filters.set('q', event.target.value || null)}
        placeholder="Nome ou descrição"
      />
      <TextField
        label="Preço mínimo"
        name="min"
        inputMode="decimal"
        value={minPrice}
        onChange={(event) => filters.set('min', event.target.value || null)}
        placeholder="0,00"
        error={rangeInverted ? 'O mínimo não pode ser maior que o máximo.' : undefined}
      />
      <TextField
        label="Preço máximo"
        name="max"
        inputMode="decimal"
        value={maxPrice}
        onChange={(event) => filters.set('max', event.target.value || null)}
        placeholder="0,00"
      />
      <Checkbox
        label="Somente disponíveis"
        name="available"
        className={filterStyles.alignWithControl}
        checked={availableOnly}
        onChange={(event) => filters.set('available', event.target.checked ? 'true' : null)}
      />
    </FilterBar>
  )

  return (
    <Page width="wide">
      <PageHeader title="Catálogo" subtitle="Produtos publicados pelas lojas do Market Hub." />

      <div className={styles.layout}>
        <div className={styles.rail}>{filterRail}</div>

        <div className={styles.results}>
          {state.status === 'loading' && (
            <ul className={styles.grid} aria-busy="true" aria-label="Carregando produtos">
              {Array.from({ length: 8 }, (_, index) => (
                <li key={index}>
                  <Skeleton variant="product" />
                </li>
              ))}
            </ul>
          )}

          {state.status === 'error' && <ErrorState message={state.error} onRetry={state.retry} />}

          {state.status === 'success' && (
            <>
              <div className={styles.resultsBar}>
                {/* Regiao viva: sem isto, aplicar um filtro nao avisa quem
                    usa leitor de tela que a lista mudou. */}
                <p className={styles.count} role="status" aria-live="polite">
                  {countLabel(total)}
                </p>
                <SelectField
                  label="Ordenar por"
                  name="sort"
                  value={filters.get('sort')}
                  options={CATALOG_SORT_OPTIONS}
                  onChange={(event) => filters.set('sort', event.target.value || null)}
                  fieldClassName={styles.sort}
                />
              </div>

              {rows.length === 0 && <EmptyState title="Nenhum produto no catálogo ainda." />}

              {rows.length > 0 && total === 0 && (
                <EmptyState
                  title="Nenhum produto corresponde aos filtros."
                  description="Tente outro termo, amplie a faixa de preço ou remova um filtro."
                  action={
                    hasFilters ? (
                      <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={filters.clearAll}
                      >
                        Limpar filtros
                      </Button>
                    ) : undefined
                  }
                />
              )}

              {total > 0 && (
                <>
                  <ul className={styles.grid}>
                    {pageRows.map((row) => (
                      <ProductCard key={row.product.id} row={row} />
                    ))}
                  </ul>
                  {total > PAGE_SIZE && (
                    <Pagination
                      page={page}
                      pageSize={PAGE_SIZE}
                      total={total}
                      onPageChange={(next) => filters.set('page', String(next))}
                    />
                  )}
                </>
              )}
            </>
          )}
        </div>
      </div>
    </Page>
  )
}
