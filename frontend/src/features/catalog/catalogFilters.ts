import type { CatalogRow } from './catalogRows'

export interface CatalogFilterValues {
  search: string
  minPrice: string
  maxPrice: string
  availableOnly: boolean
}

/**
 * Texto comparavel: sem acento e sem caixa.
 *
 * Sem isto, "relogio" nao acha "Relógio" e quem digita com acento nao acha
 * o que foi cadastrado sem.
 */
export function normalizeText(value: string): string {
  return value
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase()
    .trim()
}

/** Numero valido e nao negativo, ou `null` quando o campo nao vale como filtro. */
export function parsePriceInput(value: string): number | null {
  const trimmed = value.trim().replace(',', '.')
  if (!trimmed) {
    return null
  }
  const parsed = Number(trimmed)
  if (!Number.isFinite(parsed) || parsed < 0) {
    return null
  }
  return parsed
}

/** Faixa invertida nao filtra: a tela mostra erro no campo e mantem a lista. */
export function isPriceRangeInverted(minPrice: string, maxPrice: string): boolean {
  const min = parsePriceInput(minPrice)
  const max = parsePriceInput(maxPrice)
  return min !== null && max !== null && min > max
}

export function applyCatalogFilters(rows: CatalogRow[], values: CatalogFilterValues): CatalogRow[] {
  const term = normalizeText(values.search)
  const inverted = isPriceRangeInverted(values.minPrice, values.maxPrice)
  const min = inverted ? null : parsePriceInput(values.minPrice)
  const max = inverted ? null : parsePriceInput(values.maxPrice)
  const hasPriceFilter = min !== null || max !== null

  return rows.filter((row) => {
    if (term) {
      const haystack = normalizeText(`${row.product.name} ${row.product.description ?? ''}`)
      if (!haystack.includes(term)) {
        return false
      }
    }

    if (values.availableOnly && !row.inStock) {
      return false
    }

    if (hasPriceFilter) {
      // Filtrar por preco exclui quem nao tem preco: nao da para dizer se
      // um produto sem oferta comprável cabe na faixa.
      if (row.lowestPrice === null) {
        return false
      }
      const price = Number(row.lowestPrice)
      if (min !== null && price < min) {
        return false
      }
      if (max !== null && price > max) {
        return false
      }
    }

    return true
  })
}
