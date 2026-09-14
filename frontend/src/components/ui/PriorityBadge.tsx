import { PRIORITY_LABELS } from '../../features/ops/priority'
import type { EffectivePriority } from '../../types/conversation'

/** Distinto do StatusBadge de Order Item: prioridade nao e status de pedido. */
export function PriorityBadge({ priority }: { priority: EffectivePriority }) {
  return (
    <span className={`priority-badge priority-${priority}`}>{PRIORITY_LABELS[priority]}</span>
  )
}
