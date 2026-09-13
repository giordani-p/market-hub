import { ApiRequestError } from '../api/client'

export function errorMessage(err: unknown): string {
  if (err instanceof ApiRequestError) {
    return err.message
  }
  return 'Não foi possível completar a operação.'
}
