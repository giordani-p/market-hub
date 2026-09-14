import type { ReactNode } from 'react'
import styles from './Card.module.css'

interface CardProps {
  children: ReactNode
  /** Realce de hover, para card que e alvo de link. */
  interactive?: boolean
  className?: string
}

export function Card({ children, interactive = false, className = '' }: CardProps) {
  return (
    <div className={`${styles.card} ${interactive ? styles.interactive : ''} ${className}`.trim()}>
      {children}
    </div>
  )
}
