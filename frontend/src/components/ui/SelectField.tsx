import type { SelectHTMLAttributes } from 'react'
import { Field } from './Field'
import styles from './Field.module.css'

export interface SelectOption {
  value: string
  label: string
}

interface SelectFieldProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'id'> {
  label: string
  name: string
  id?: string
  hint?: string
  error?: string
  options: SelectOption[]
  fieldClassName?: string
}

export function SelectField({
  label,
  name,
  id,
  hint,
  error,
  options,
  fieldClassName,
  className = '',
  ...props
}: SelectFieldProps) {
  return (
    <Field id={id ?? name} label={label} hint={hint} error={error} className={fieldClassName}>
      {(control) => (
        <select
          {...control}
          name={name}
          className={`${styles.control} ${styles.select} ${className}`.trim()}
          {...props}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      )}
    </Field>
  )
}
