import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import styles from './SummaryStat.module.css'

interface SummaryStatProps {
  label: string
  value: number
  to: string
  accent?: boolean
}

export function SummaryStat({ label, value, to, accent = false }: SummaryStatProps) {
  return (
    <Link to={to} className={`${styles.stat} ${accent ? styles.accent : ''}`.trim()}>
      <span className={styles.value}>{value}</span>
      <span className={styles.label}>{label}</span>
    </Link>
  )
}

export function SummaryGrid({ children }: { children: ReactNode }) {
  return <div className={styles.summaryGrid}>{children}</div>
}
