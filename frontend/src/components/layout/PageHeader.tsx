import type { ReactNode } from 'react'
import { Breadcrumbs, type Crumb } from './Breadcrumbs'
import styles from './PageHeader.module.css'

interface PageHeaderProps {
  title: string
  subtitle?: string
  breadcrumbs?: Crumb[]
  /** Badges ou tags que qualificam o titulo (status, prioridade). */
  meta?: ReactNode
  /** Acao principal da tela, alinhada a direita. */
  actions?: ReactNode
}

/**
 * Cabecalho unico de tela. O `id` fixo e o alvo do foco depois de cada
 * navegacao -- ver `useRouteFocus`.
 */
export function PageHeader({ title, subtitle, breadcrumbs, meta, actions }: PageHeaderProps) {
  return (
    <header className={styles.pageHeader}>
      {breadcrumbs && breadcrumbs.length > 0 && <Breadcrumbs items={breadcrumbs} />}
      <div className={styles.row}>
        {/* Subtitulo dentro da coluna do titulo: solto depois da linha, ele
            caia embaixo da acao quando o header quebrava em telefone. */}
        <div className={styles.headingBlock}>
          <div className={styles.heading}>
            <h1 className={styles.title} id="page-title" tabIndex={-1}>
              {title}
            </h1>
            {meta}
          </div>
          {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
        </div>
        {actions && <div className={styles.actions}>{actions}</div>}
      </div>
    </header>
  )
}
