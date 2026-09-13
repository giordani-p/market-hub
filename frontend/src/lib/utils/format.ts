export function formatCurrencyBRL(value: string): string {
  const amount = Number(value)
  if (Number.isNaN(amount)) {
    return value
  }
  return amount.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export function formatDate(value: string): string {
  return new Date(value).toLocaleDateString('pt-BR')
}
