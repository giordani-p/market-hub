import { useCallback, useEffect, useState } from 'react'
import { errorMessage } from './errorMessage'

type AsyncState<T> =
  { status: 'loading' } | { status: 'error'; error: string } | { status: 'success'; data: T }

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [state, setState] = useState<AsyncState<T>>({ status: 'loading' })
  const [tick, setTick] = useState(0)

  const load = useCallback(() => {
    setState({ status: 'loading' })
    fn()
      .then((data) => setState({ status: 'success', data }))
      .catch((err: unknown) => setState({ status: 'error', error: errorMessage(err) }))
    // deps controlam quando refazer a chamada; tick força retry manual.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick])

  useEffect(() => {
    load()
  }, [load])

  const retry = useCallback(() => setTick((value) => value + 1), [])

  return { ...state, retry }
}
