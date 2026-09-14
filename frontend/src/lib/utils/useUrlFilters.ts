import { useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'

export interface UrlFilters {
  get: (key: string) => string
  set: (key: string, value: string | null) => void
  clearAll: () => void
  /** Quantos filtros estao aplicados, entre as chaves informadas. */
  countActive: (keys: string[]) => number
}

/**
 * Filtros na query string.
 *
 * A URL passa a ser a fonte de verdade de qualquer filtro de lista: a tela
 * filtrada vira um link, o botao voltar desfaz o filtro e recarregar a
 * pagina nao perde o contexto.
 */
export function useUrlFilters(): UrlFilters {
  const [searchParams, setSearchParams] = useSearchParams()

  const set = useCallback(
    (key: string, value: string | null) => {
      setSearchParams(
        (current) => {
          const next = new URLSearchParams(current)
          if (value) {
            next.set(key, value)
          } else {
            next.delete(key)
          }
          // Trocar um filtro sempre volta para a primeira pagina.
          if (key !== 'page') {
            next.delete('page')
          }
          return next
        },
        { replace: true },
      )
    },
    [setSearchParams],
  )

  const clearAll = useCallback(() => {
    setSearchParams(new URLSearchParams(), { replace: true })
  }, [setSearchParams])

  const get = useCallback((key: string) => searchParams.get(key) ?? '', [searchParams])

  const countActive = useCallback(
    (keys: string[]) => keys.filter((key) => searchParams.get(key)).length,
    [searchParams],
  )

  return { get, set, clearAll, countActive }
}

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

/** O backend so aceita ID exato; validar antes evita um fetch que ja nasce 422. */
export function isCompleteUuid(value: string): boolean {
  return UUID_PATTERN.test(value.trim())
}
