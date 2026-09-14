import { describe, expect, it, vi } from 'vitest'
import { resolveNotificationRoute } from './resolveRoute'

function notification(entityType: 'ORDER_ITEM' | 'CONVERSATION', entityId: string) {
  return { entity_type: entityType, entity_id: entityId }
}

describe('resolveNotificationRoute', () => {
  it('routes seller + ORDER_ITEM directly, without any fetch', async () => {
    const fetchOrderItem = vi.fn()
    const fetchConversation = vi.fn()

    const path = await resolveNotificationRoute('seller', notification('ORDER_ITEM', 'item-1'), {
      fetchOrderItem,
      fetchConversation,
    })

    expect(path).toBe('/seller/orders/item-1')
    expect(fetchOrderItem).not.toHaveBeenCalled()
    expect(fetchConversation).not.toHaveBeenCalled()
  })

  it('routes seller + CONVERSATION via the conversation lookup', async () => {
    const fetchOrderItem = vi.fn()
    const fetchConversation = vi.fn().mockResolvedValue({ id: 'conv-1', order_item_id: 'item-1' })

    const path = await resolveNotificationRoute('seller', notification('CONVERSATION', 'conv-1'), {
      fetchOrderItem,
      fetchConversation,
    })

    expect(path).toBe('/seller/orders/item-1')
    expect(fetchConversation).toHaveBeenCalledWith('conv-1')
    expect(fetchOrderItem).not.toHaveBeenCalled()
  })

  it('routes buyer + ORDER_ITEM via the order item lookup (needs order_id)', async () => {
    const fetchOrderItem = vi.fn().mockResolvedValue({ id: 'item-1', order: { id: 'order-1' } })
    const fetchConversation = vi.fn()

    const path = await resolveNotificationRoute('buyer', notification('ORDER_ITEM', 'item-1'), {
      fetchOrderItem,
      fetchConversation,
    })

    expect(path).toBe('/buyer/orders/order-1/items/item-1')
    expect(fetchOrderItem).toHaveBeenCalledWith('item-1')
    expect(fetchConversation).not.toHaveBeenCalled()
  })

  it('routes buyer + CONVERSATION via conversation then order item lookup', async () => {
    const fetchConversation = vi.fn().mockResolvedValue({ id: 'conv-1', order_item_id: 'item-1' })
    const fetchOrderItem = vi.fn().mockResolvedValue({ id: 'item-1', order: { id: 'order-1' } })

    const path = await resolveNotificationRoute('buyer', notification('CONVERSATION', 'conv-1'), {
      fetchOrderItem,
      fetchConversation,
    })

    expect(path).toBe('/buyer/orders/order-1/items/item-1')
    expect(fetchConversation).toHaveBeenCalledWith('conv-1')
    expect(fetchOrderItem).toHaveBeenCalledWith('item-1')
  })

  it('routes ops + CONVERSATION directly, without any fetch', async () => {
    const fetchOrderItem = vi.fn()
    const fetchConversation = vi.fn()

    const path = await resolveNotificationRoute('ops', notification('CONVERSATION', 'conv-9'), {
      fetchOrderItem,
      fetchConversation,
    })

    expect(path).toBe('/ops/conversations/conv-9')
    expect(fetchOrderItem).not.toHaveBeenCalled()
    expect(fetchConversation).not.toHaveBeenCalled()
  })
})
