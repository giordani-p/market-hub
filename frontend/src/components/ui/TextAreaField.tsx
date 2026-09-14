import type { TextareaHTMLAttributes } from 'react'
import { Field } from './Field'
import styles from './Field.module.css'

interface TextAreaFieldProps extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'id'> {
  label: string
  name: string
  id?: string
  hint?: string
  error?: string
  fieldClassName?: string
}

export function TextAreaField({
  label,
  name,
  id,
  hint,
  error,
  fieldClassName,
  className = '',
  rows = 3,
  ...props
}: TextAreaFieldProps) {
  return (
    <Field id={id ?? name} label={label} hint={hint} error={error} className={fieldClassName}>
      {(control) => (
        <textarea
          {...control}
          name={name}
          rows={rows}
          className={`${styles.control} ${styles.textarea} ${className}`.trim()}
          {...props}
        />
      )}
    </Field>
  )
}
