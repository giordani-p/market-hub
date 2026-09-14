export type InternalCommentAuthorType = 'ops' | 'seller'

export interface InternalComment {
  id: string
  order_item_id: string
  author_id: string
  author_type: InternalCommentAuthorType
  content: string
  created_at: string
}
