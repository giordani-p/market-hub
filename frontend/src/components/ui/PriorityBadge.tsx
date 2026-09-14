import { AlertTriangle } from 'lucide-react'
import { PRIORITY_LABELS } from '../../features/ops/priority'
import type { EffectivePriority } from '../../types/conversation'

/** Distinto do StatusBadge de Order Item: prioridade nao e status de pedido.
 *  So `critical` ganha icone (AlertTriangle) -- e o unico nivel que pede
 *  "destaque forte" (skill secao 11); os demais ja se diferenciam por cor. */
export function PriorityBadge({ priority }: { priority: EffectivePriority }) {
  return (
    <span className={`priority-badge priority-${priority}`}>
      {priority === 'critical' && <AlertTriangle size={14} aria-hidden="true" />}
      {PRIORITY_LABELS[priority]}
    </span>
  )
}
