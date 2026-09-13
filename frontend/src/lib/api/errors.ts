export interface ApiError {
  status: number
  code: string
  message: string
}

interface DomainErrorBody {
  code: string
  message: string
}

interface ValidationErrorBody {
  detail: Array<{ msg: string; loc: (string | number)[] }>
}

function isDomainErrorBody(body: unknown): body is DomainErrorBody {
  return (
    typeof body === 'object' &&
    body !== null &&
    typeof (body as Record<string, unknown>).code === 'string' &&
    typeof (body as Record<string, unknown>).message === 'string'
  )
}

function isValidationErrorBody(body: unknown): body is ValidationErrorBody {
  return (
    typeof body === 'object' &&
    body !== null &&
    Array.isArray((body as Record<string, unknown>).detail)
  )
}

/** Normaliza os dois formatos de erro do backend: `ErrorResponse` e o 422 do FastAPI. */
export function normalizeErrorBody(status: number, body: unknown): ApiError {
  if (isDomainErrorBody(body)) {
    return { status, code: body.code, message: body.message }
  }
  if (isValidationErrorBody(body)) {
    const message = body.detail.map((item) => item.msg).join('; ') || 'Validation error'
    return { status, code: 'validation_error', message }
  }
  return { status, code: 'unknown_error', message: 'Unexpected error' }
}
