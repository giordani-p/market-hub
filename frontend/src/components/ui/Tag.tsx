import type { ReactNode } from 'react'
import styles from './Tag.module.css'

export type TagTone =
  'neutral' | 'muted' | 'info' | 'success' | 'danger' | 'warning' | 'dangerSolid'

interface TagProps {
  tone?: TagTone
  /** Marcador redondo para estado que nao tem icone proprio. */
  dot?: boolean
  children: ReactNode
  className?: string
}

export function Tag({ tone = 'neutral', dot = false, children, className = '' }: TagProps) {
  return (
    <span className={`${styles.tag} ${styles[tone]} ${className}`.trim()}>
      {dot && <span className={styles.dot} aria-hidden="true" />}
      {children}
    </span>
  )
}
