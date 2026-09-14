import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { OpsConversation } from '../../types/ops'
import { PriorityActions } from './PriorityActions'
import { renderWithProviders } from '../../test/renderWithProviders'

const { refreshOpsPriority, applyOpsCritical, removeOpsCritical } = vi.hoisted(() => ({
  refreshOpsPriority: vi.fn(),
  applyOpsCritical: vi.fn(),
  removeOpsCritical: vi.fn(),
}))

vi.mock('./api', () => ({ refreshOpsPriority, applyOpsCritical, removeOpsCritical }))

function conversation(overrides: Partial<OpsConversation> = {}): OpsConversation {
  return {
    id: 'conversation-1',
    order_item_id: 'item-1',
    reason: 'atraso',
    status: 'open',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    last_interaction_at: '2026-01-01T00:00:00Z',
    calculated_priority: 'high',
    ops_override: null,
    effective_priority: 'high',
    ...overrides,
  }
}

describe('PriorityActions', () => {
  afterEach(() => {
    refreshOpsPriority.mockReset()
    applyOpsCritical.mockReset()
    removeOpsCritical.mockReset()
  })

  it('offers to mark as critical when there is no override yet', () => {
    renderWithProviders(<PriorityActions conversation={conversation()} onChanged={vi.fn()} />)

    expect(screen.getByRole('button', { name: 'Marcar como critical' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Remover critical' })).not.toBeInTheDocument()
  })

  it('offers to remove the override when already critical', () => {
    renderWithProviders(
      <PriorityActions
        conversation={conversation({ ops_override: 'critical', effective_priority: 'critical' })}
        onChanged={vi.fn()}
      />,
    )

    expect(screen.getByRole('button', { name: 'Remover critical' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Marcar como critical' })).not.toBeInTheDocument()
  })

  it('recalculates priority and notifies the parent', async () => {
    refreshOpsPriority.mockResolvedValue(undefined)
    const onChanged = vi.fn()
    renderWithProviders(<PriorityActions conversation={conversation()} onChanged={onChanged} />)
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: 'Recalcular prioridade' }))

    expect(refreshOpsPriority).toHaveBeenCalledWith('conversation-1')
    expect(onChanged).toHaveBeenCalledOnce()
  })

  it('requires a justification before applying critical', async () => {
    applyOpsCritical.mockResolvedValue(undefined)
    const onChanged = vi.fn()
    renderWithProviders(<PriorityActions conversation={conversation()} onChanged={onChanged} />)
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: 'Marcar como critical' }))
    expect(screen.getByRole('button', { name: 'Confirmar' })).toBeDisabled()

    await user.type(screen.getByPlaceholderText('Justificativa (obrigatória)'), 'Cliente VIP.')
    await user.click(screen.getByRole('button', { name: 'Confirmar' }))

    expect(applyOpsCritical).toHaveBeenCalledWith('conversation-1', 'Cliente VIP.')
    expect(onChanged).toHaveBeenCalledOnce()
  })

  it('removes the critical override without a justification', async () => {
    removeOpsCritical.mockResolvedValue(undefined)
    const onChanged = vi.fn()
    renderWithProviders(
      <PriorityActions
        conversation={conversation({ ops_override: 'critical', effective_priority: 'critical' })}
        onChanged={onChanged}
      />,
    )
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: 'Remover critical' }))

    expect(removeOpsCritical).toHaveBeenCalledWith('conversation-1')
    expect(onChanged).toHaveBeenCalledOnce()
  })
})
