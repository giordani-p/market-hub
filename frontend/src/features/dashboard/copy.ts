import type { BuyerOrderProjectionStatus } from '../../types/dashboard'

export const BUYER_ORDER_STATUS_LABELS: Record<BuyerOrderProjectionStatus, string> = {
  in_progress: 'Em andamento',
  completed: 'Concluído',
  cancelled: 'Cancelado',
}
