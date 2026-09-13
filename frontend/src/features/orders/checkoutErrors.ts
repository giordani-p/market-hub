import type { CheckoutRejectReason } from '../../types/order'

const REASON_LABELS: Record<CheckoutRejectReason, string> = {
  not_found: 'Esta oferta não existe mais.',
  unavailable: 'Esta oferta está indisponível no momento.',
  insufficient_stock: 'Estoque insuficiente para a quantidade escolhida.',
  price_changed: 'O preço da oferta mudou. Atualize a página e tente novamente.',
}

export function checkoutRejectReasonLabel(reason: CheckoutRejectReason): string {
  return REASON_LABELS[reason] ?? 'Não foi possível concluir a compra deste item.'
}
