import type { ConversationReason } from '../../types/conversation'

export const CONVERSATION_REASON_LABELS: Record<ConversationReason, string> = {
  atraso: 'Atraso',
  troca: 'Troca',
  devolucao: 'Devolução',
  reclamacao: 'Reclamação',
  suporte: 'Suporte',
  elogio: 'Elogio',
  outros: 'Outros',
}

export const CONVERSATION_REASONS = Object.keys(CONVERSATION_REASON_LABELS) as ConversationReason[]
