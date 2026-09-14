import type { CatalogRow } from './catalogRows'

export type CatalogSort = 'relevance' | 'price_asc' | 'price_desc' | 'name_asc'

export const CATALOG_SORT_OPTIONS: { value: string; label: string }[] = [
  { value: '', label: 'Mais relevantes' },
  { value: 'price_asc', label: 'Menor preço' },
  { value: 'price_desc', label: 'Maior preço' },
  { value: 'name_asc', label: 'Nome (A-Z)' },
]

const SORT_VALUES: CatalogSort[] = ['price_asc', 'price_desc', 'name_asc']

export function parseCatalogSort(value: string): CatalogSort {
  return SORT_VALUES.includes(value as CatalogSort) ? (value as CatalogSort) : 'relevance'
}

/**
 * Ordena as linhas do catalogo.
 *
 * Produto sem oferta comprável vai sempre para o fim nas duas ordenacoes
 * por preco, nas duas direcoes: jogar "sem preco" para o topo de "maior
 * preco" seria coerente e inutil.
 */
export function sortCatalogRows(rows: CatalogRow[], sort: CatalogSort): CatalogRow[] {
  if (sort === 'relevance') {
    // Ordem em que a API devolveu.
    return rows
  }

  const sorted = [...rows]

  if (sort === 'name_asc') {
    return sorted.sort((a, b) => a.product.name.localeCompare(b.product.name, 'pt-BR'))
  }

  const direction = sort === 'price_asc' ? 1 : -1
  return sorted.sort((a, b) => {
    if (a.lowestPrice === null && b.lowestPrice === null) {
      return 0
    }
    if (a.lowestPrice === null) {
      return 1
    }
    if (b.lowestPrice === null) {
      return -1
    }
    return (Number(a.lowestPrice) - Number(b.lowestPrice)) * direction
  })
}
