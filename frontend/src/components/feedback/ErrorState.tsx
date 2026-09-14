import { AlertCircle } from 'lucide-react'
import { Button } from '../ui/Button'
import styles from './ErrorState.module.css'

interface ErrorStateProps {
  message: string
  onRetry?: () => void
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className={styles.errorState} role="alert">
      <AlertCircle size={20} className={styles.icon} aria-hidden="true" />
      <p className={styles.message}>{message}</p>
      {onRetry && (
        <Button type="button" variant="secondary" size="sm" onClick={onRetry}>
          Tentar novamente
        </Button>
      )}
    </div>
  )
}
