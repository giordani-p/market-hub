/** Converte input livre para o Price do contrato (`"10.00"`). */
export function toApiPrice(value: string): string | null {
  const normalized = value.trim().replace(',', '.')
  if (normalized === '') {
    return null
  }
  const amount = Number(normalized)
  if (!Number.isFinite(amount) || amount < 0) {
    return null
  }
  return amount.toFixed(2)
}
