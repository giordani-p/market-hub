import { describe, expect, it } from 'vitest'
import type { AppNotification } from '../../types/notification'
import { buildNotificationCopy } from './copy'

function notification(overrides: Partial<AppNotification> = {}): AppNotification {
  return {
    id: 'notif-1',
    recipient_id: 'user-1',
    type: 'ORDER_ITEM_STATUS_CHANGED',
    title: 'raw english title',
    message: 'raw english message',
    entity_type: 'ORDER_ITEM',
    entity_id: 'item-1',
    metadata: { previous_status: 'placed', new_status: 'preparing' },
    created_at: '2026-01-01T00:00:00Z',
    read_at: null,
    ...overrides,
  }
}

describe('buildNotificationCopy', () => {
  it('builds a friendly copy for order item delivered', () => {
    const copy = buildNotificationCopy(
      notification({ metadata: { previous_status: 'in_transit', new_status: 'delivered' } }),
    )
    expect(copy).toEqual({ title: 'Pedido entregue', message: 'Seu pedido foi entregue.' })
  })

  it('builds a friendly copy for order item cancelled', () => {
    const copy = buildNotificationCopy(
      notification({ metadata: { previous_status: 'placed', new_status: 'cancelled' } }),
    )
    expect(copy).toEqual({ title: 'Pedido cancelado', message: 'Seu pedido foi cancelado.' })
  })

  it('builds a generic status copy for other order item transitions, using the PT-BR label', () => {
    const copy = buildNotificationCopy(
      notification({ metadata: { previous_status: 'placed', new_status: 'preparing' } }),
    )
    expect(copy).toEqual({
      title: 'Status do pedido atualizado',
      message: 'Seu pedido agora está "Em preparação".',
    })
  })

  it('builds a copy for conversation closed', () => {
    const copy = buildNotificationCopy(
      notification({
        type: 'CONVERSATION_STATUS_CHANGED',
        entity_type: 'CONVERSATION',
        entity_id: 'conv-1',
        metadata: { previous_status: 'open', new_status: 'closed' },
      }),
    )
    expect(copy).toEqual({
      title: 'Conversa encerrada',
      message: 'A conversa sobre este pedido foi encerrada.',
    })
  })

  it('builds a copy for priority changed to critical', () => {
    const copy = buildNotificationCopy(
      notification({
        type: 'CONVERSATION_PRIORITY_CHANGED',
        entity_type: 'CONVERSATION',
        entity_id: 'conv-1',
        metadata: { previous_status: 'medium', new_status: 'critical' },
      }),
    )
    expect(copy).toEqual({
      title: 'Prioridade crítica',
      message: 'Uma conversa foi marcada como prioridade crítica.',
    })
  })

  it('builds a generic priority copy for other transitions, using the PT-BR label', () => {
    const copy = buildNotificationCopy(
      notification({
        type: 'CONVERSATION_PRIORITY_CHANGED',
        entity_type: 'CONVERSATION',
        entity_id: 'conv-1',
        metadata: { previous_status: 'critical', new_status: 'medium' },
      }),
    )
    expect(copy).toEqual({
      title: 'Prioridade atualizada',
      message: 'A prioridade da conversa mudou para "Média".',
    })
  })

  it('falls back to a generic copy for an unknown type, ignoring the raw backend text', () => {
    // @ts-expect-error tipo invalido de proposito, pra testar o fallback
    const copy = buildNotificationCopy(notification({ type: 'SOMETHING_NEW' }))
    expect(copy).toEqual({ title: 'Atualização', message: 'Você tem uma atualização.' })
  })
})
