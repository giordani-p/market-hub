import styles from './Skeleton.module.css'

type SkeletonVariant = 'text' | 'card' | 'row' | 'stat'

interface SkeletonProps {
  variant?: SkeletonVariant
  width?: string
}

export function Skeleton({ variant = 'text', width }: SkeletonProps) {
  return (
    <span
      className={`${styles.skeleton} ${styles[variant]}`}
      style={width ? { width } : undefined}
    />
  )
}

interface SkeletonListProps {
  count?: number
  variant?: SkeletonVariant
  label?: string
}

/**
 * Grupo de placeholders. Anuncia o carregamento uma vez so, em vez de
 * deixar cada barra virar ruido para o leitor de tela.
 */
export function SkeletonList({
  count = 5,
  variant = 'card',
  label = 'Carregando...',
}: SkeletonListProps) {
  return (
    <div className={styles.stack} role="status" aria-live="polite" aria-busy="true">
      <span className="sr-only">{label}</span>
      {Array.from({ length: count }, (_, index) => (
        <Skeleton key={index} variant={variant} />
      ))}
    </div>
  )
}
