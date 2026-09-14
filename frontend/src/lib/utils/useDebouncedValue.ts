import { useEffect, useState } from 'react'

/**
 * Versao atrasada de um valor.
 *
 * Usada nos campos de texto das listas: antes cada tecla disparava um
 * fetch, e uma busca de 8 caracteres virava 8 requisicoes.
 */
export function useDebouncedValue<T>(value: T, delayMs = 300): T {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delayMs)
    return () => window.clearTimeout(timer)
  }, [value, delayMs])

  return debounced
}
