import { apiRequest } from '../../lib/api/client'
import type { InternalComment } from '../../types/support'

export function fetchInternalComments(itemId: string): Promise<InternalComment[]> {
  return apiRequest<InternalComment[]>(`/order-items/${itemId}/internal-comments`)
}

export function createInternalComment(itemId: string, content: string): Promise<InternalComment> {
  return apiRequest<InternalComment>(`/order-items/${itemId}/internal-comments`, {
    method: 'POST',
    body: { content },
  })
}
