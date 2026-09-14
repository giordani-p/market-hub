import { AlertCircle } from 'lucide-react'
import styles from './FormError.module.css'

/**
 * Erro de uma acao pontual, exibido ao lado do controle que a disparou.
 *
 * Sucesso vai para o Toast; erro fica inline, perto de onde a pessoa pode
 * corrigir e tentar de novo.
 */
export function FormError({ message }: { message: string | null }) {
  if (!message) {
    return null
  }
  return (
    <p className={styles.formError} role="alert">
      <AlertCircle size={16} aria-hidden="true" />
      {message}
    </p>
  )
}
