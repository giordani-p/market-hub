import { Link } from 'react-router-dom'

interface SummaryStatProps {
  label: string
  value: number
  to: string
  accent?: boolean
}

export function SummaryStat({ label, value, to, accent = false }: SummaryStatProps) {
  return (
    <Link to={to} className={`summary-stat${accent ? ' summary-stat-accent' : ''}`}>
      <span className="summary-stat-value">{value}</span>
      <span className="summary-stat-label">{label}</span>
    </Link>
  )
}
