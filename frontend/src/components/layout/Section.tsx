import type { ReactNode } from 'react'
import styles from './Section.module.css'

interface SectionProps {
  title: string
  description?: string
  /** Link ou botao alinhado ao titulo ("Ver fila completa", "Nova oferta"). */
  action?: ReactNode
  children: ReactNode
}

export function Section({ title, description, action, children }: SectionProps) {
  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <h2>{title}</h2>
        {action}
      </div>
      {description && <p className={styles.description}>{description}</p>}
      {children}
    </section>
  )
}
