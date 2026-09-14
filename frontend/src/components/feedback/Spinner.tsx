import styles from './Spinner.module.css'

export function Spinner({ label = 'Carregando...' }: { label?: string }) {
  return (
    <div className={styles.spinner} role="status" aria-live="polite">
      <span className={styles.circle} aria-hidden="true" />
      <span>{label}</span>
    </div>
  )
}
