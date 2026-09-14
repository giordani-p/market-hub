import { SlidersHorizontal, X } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { Button } from '../ui/Button'
import styles from './FilterBar.module.css'

export interface ActiveFilter {
  /** Chave estavel do filtro, usada so como key de render. */
  key: string
  label: string
  onRemove: () => void
}

interface FilterBarProps {
  children: ReactNode
  active?: ActiveFilter[]
  onClearAll?: () => void
}

/**
 * Agrupa os campos de filtro e resume o que esta aplicado em chips
 * removiveis -- antes nao havia nenhuma forma de ver, de relance, por que
 * a lista estava curta.
 */
export function FilterBar({ children, active = [], onClearAll }: FilterBarProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <section className={styles.filterBar} aria-label="Filtros">
      <Button
        type="button"
        variant="secondary"
        size="sm"
        className={styles.toggle}
        onClick={() => setExpanded((value) => !value)}
        aria-expanded={expanded}
      >
        <SlidersHorizontal size={16} aria-hidden="true" />
        Filtros
        {active.length > 0 && ` (${active.length})`}
      </Button>

      <div className={`${styles.fields} ${expanded ? '' : styles.fieldsCollapsed}`.trim()}>
        {children}
      </div>

      {active.length > 0 && (
        <div className={styles.chips}>
          <span className={styles.chipsLabel}>Filtros ativos</span>
          {active.map((filter) => (
            <button
              key={filter.key}
              type="button"
              className={styles.chip}
              onClick={filter.onRemove}
              aria-label={`Remover filtro ${filter.label}`}
            >
              {filter.label}
              <X size={12} aria-hidden="true" />
            </button>
          ))}
          {active.length > 1 && onClearAll && (
            <Button type="button" variant="tertiary" size="sm" onClick={onClearAll}>
              Limpar filtros
            </Button>
          )}
        </div>
      )}
    </section>
  )
}
