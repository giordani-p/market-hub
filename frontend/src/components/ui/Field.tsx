import type { ReactNode } from 'react'
import styles from './Field.module.css'

/** Props que o Field injeta no controle, ja resolvendo a associacao a11y. */
export interface FieldControlProps {
  id: string
  'aria-describedby': string | undefined
  'aria-invalid': boolean | undefined
}

interface FieldProps {
  id: string
  label: string
  hint?: string
  error?: string
  className?: string
  children: (control: FieldControlProps) => ReactNode
}

/**
 * Envolve label, hint e erro de qualquer controle de formulario.
 *
 * Existe para que a associacao entre rotulo, descricao e mensagem de erro
 * seja feita em um lugar so -- antes cada tela montava a sua e select e
 * checkbox ficavam sem associacao nenhuma.
 */
export function Field({ id, label, hint, error, className = '', children }: FieldProps) {
  const hintId = hint ? `${id}-hint` : undefined
  const errorId = error ? `${id}-error` : undefined
  const describedBy = [hintId, errorId].filter(Boolean).join(' ') || undefined

  return (
    <div className={`${styles.field} ${className}`.trim()}>
      <label className={styles.label} htmlFor={id}>
        {label}
      </label>
      {children({
        id,
        'aria-describedby': describedBy,
        'aria-invalid': error ? true : undefined,
      })}
      {/* Hint depois do controle: acima dele, um campo com dica empurrava o
          proprio input para baixo e desalinhava a linha da barra de filtros. */}
      {hint && (
        <span className={styles.hint} id={hintId}>
          {hint}
        </span>
      )}
      {error && (
        <span className={styles.error} id={errorId} role="alert">
          {error}
        </span>
      )}
    </div>
  )
}
