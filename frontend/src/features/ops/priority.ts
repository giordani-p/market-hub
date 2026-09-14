import type { EffectivePriority } from '../../types/conversation'

export const PRIORITY_LABELS: Record<EffectivePriority, string> = {
  low: 'Baixa',
  medium: 'Média',
  high: 'Alta',
  critical: 'Crítica',
}

export const EFFECTIVE_PRIORITIES: EffectivePriority[] = ['critical', 'high', 'medium', 'low']
