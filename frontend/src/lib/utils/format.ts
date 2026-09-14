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

export function formatTime(value: string): string {
  return new Date(value).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

export function formatDateTime(value: string): string {
  return `${formatDate(value)} ${formatTime(value)}`
}

/** Converte um input `<input type="date">` (yyyy-mm-dd) no inicio do dia em UTC. */
export function toDayStartUTC(date: string): string {
  return `${date}T00:00:00Z`
}

/** Converte um input `<input type="date">` (yyyy-mm-dd) no fim do dia em UTC. */
export function toDayEndUTC(date: string): string {
  return `${date}T23:59:59Z`
}
