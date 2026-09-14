import type { InputHTMLAttributes } from 'react'
import styles from './Field.module.css'

interface ChoiceProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: string
}

/** Checkbox e Radio compartilham a caixa: o alvo de toque e o rotulo inteiro. */
export function Checkbox({ label, className = '', ...props }: ChoiceProps) {
  return (
    <label className={`${styles.choice} ${className}`.trim()}>
      <input type="checkbox" {...props} />
      {label}
    </label>
  )
}

export function Radio({ label, className = '', ...props }: ChoiceProps) {
  return (
    <label className={`${styles.choice} ${className}`.trim()}>
      <input type="radio" {...props} />
      {label}
    </label>
  )
}
