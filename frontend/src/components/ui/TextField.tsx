import type { InputHTMLAttributes } from 'react'
import { Field } from './Field'
import styles from './Field.module.css'

interface TextFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'id'> {
  label: string
  name: string
  id?: string
  hint?: string
  error?: string
  fieldClassName?: string
}

export function TextField({
  label,
  name,
  id,
  hint,
  error,
  fieldClassName,
  className = '',
  ...props
}: TextFieldProps) {
  return (
    <Field id={id ?? name} label={label} hint={hint} error={error} className={fieldClassName}>
      {(control) => (
        <input
          {...control}
          name={name}
          className={`${styles.control} ${className}`.trim()}
          {...props}
        />
      )}
    </Field>
  )
}
