import { apiRequest } from '../../lib/api/client'
import type { InternalComment } from '../../types/support'

export type InternalCommentsViewerRole = 'seller' | 'ops'

function basePath(itemId: string, viewerRole: InternalCommentsViewerRole): string {
  return viewerRole === 'ops'
    ? `/ops/order-items/${itemId}/internal-comments`
    : `/order-items/${itemId}/internal-comments`
}

export function fetchInternalComments(
  itemId: string,
  viewerRole: InternalCommentsViewerRole = 'seller',
): Promise<InternalComment[]> {
  return apiRequest<InternalComment[]>(basePath(itemId, viewerRole))
}

export function createInternalComment(
  itemId: string,
  content: string,
  viewerRole: InternalCommentsViewerRole = 'seller',
): Promise<InternalComment> {
  return apiRequest<InternalComment>(basePath(itemId, viewerRole), {
    method: 'POST',
    body: { content },
  })
}
