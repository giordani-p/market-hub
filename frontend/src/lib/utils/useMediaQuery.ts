import { useCallback, useSyncExternalStore } from 'react'

/**
 * Acompanha um media query em runtime.
 *
 * Existe para os casos em que o layout muda de estrutura, nao so de
 * estilo -- paineis lado a lado que viram abas, por exemplo. Onde CSS
 * resolve, CSS resolve: nao usar isto para esconder ou mostrar coisa.
 *
 * `useSyncExternalStore` porque o media query e exatamente isso: um estado
 * que vive fora do React. Evita o par useState + useEffect e o render extra.
 */
export function useMediaQuery(query: string): boolean {
  const subscribe = useCallback(
    (onStoreChange: () => void) => {
      if (typeof window === 'undefined' || !window.matchMedia) {
        return () => {}
      }
      const mediaQueryList = window.matchMedia(query)
      mediaQueryList.addEventListener('change', onStoreChange)
      return () => mediaQueryList.removeEventListener('change', onStoreChange)
    },
    [query],
  )

  const getSnapshot = useCallback(() => {
    if (typeof window === 'undefined' || !window.matchMedia) {
      return false
    }
    return window.matchMedia(query).matches
  }, [query])

  // No servidor nao ha viewport: assume desktop, o layout mais largo.
  return useSyncExternalStore(subscribe, getSnapshot, () => false)
}
