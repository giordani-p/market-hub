import { AlertTriangle } from 'lucide-react'
import { PRIORITY_LABELS } from '../../features/ops/priority'
import type { EffectivePriority } from '../../types/conversation'
import { Tag, type TagTone } from './Tag'

/** Distinto do StatusBadge de Order Item: prioridade nao e status de pedido.
 *  So `critical` ganha icone (AlertTriangle) -- e o unico nivel que pede
 *  "destaque forte" (skill secao 11); os demais ja se diferenciam por cor. */
const PRIORITY_TONE: Record<EffectivePriority, TagTone> = {
  low: 'muted',
  medium: 'info',
  high: 'warning',
  critical: 'dangerSolid',
}

export function PriorityBadge({ priority }: { priority: EffectivePriority }) {
  return (
    <Tag tone={PRIORITY_TONE[priority]}>
      {priority === 'critical' && <AlertTriangle size={14} aria-hidden="true" />}
      {PRIORITY_LABELS[priority]}
    </Tag>
  )
}
