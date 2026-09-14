import type { Offer } from '../../types/catalog'

/** Menor preco entre ofertas compraveis. So apresentacao — nao e regra de dominio. */
export function lowestAvailablePrice(offers: Offer[]): string | null {
  const available = offers.filter((offer) => offer.available && offer.stock > 0)
  if (available.length === 0) {
    return null
  }
  return available.reduce(
    (lowest, offer) => (Number(offer.price) < Number(lowest) ? offer.price : lowest),
    available[0].price,
  )
}
