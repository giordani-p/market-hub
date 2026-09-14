import type { InputHTMLAttributes, ReactNode } from 'react'
import { Field } from './Field'
import styles from './Field.module.css'

interface TextFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'id'> {
  label: string
  name: string
  id?: string
  hint?: string
  error?: string
  /** Acao dentro da caixa do campo, a direita (mostrar senha, por exemplo). */
  trailing?: ReactNode
  fieldClassName?: string
}

export function TextField({
  label,
  name,
  id,
  hint,
  error,
  trailing,
  fieldClassName,
  className = '',
  ...props
}: TextFieldProps) {
  return (
    <Field id={id ?? name} label={label} hint={hint} error={error} className={fieldClassName}>
      {(control) => {
        const input = (
          <input
            {...control}
            name={name}
            className={`${styles.control} ${className}`.trim()}
            {...props}
          />
        )
        if (!trailing) {
          return input
        }
        return (
          <span className={styles.controlWrap}>
            {input}
            <span className={styles.trailing}>{trailing}</span>
          </span>
        )
      }}
    </Field>
  )
}
