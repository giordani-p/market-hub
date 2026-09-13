import type { InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
}

export function Input({ label, error, id, name, className = '', ...props }: InputProps) {
  const inputId = id ?? name
  return (
    <div className="field">
      <label htmlFor={inputId}>{label}</label>
      <input id={inputId} name={name} className={`input ${className}`.trim()} {...props} />
      {error && (
        <span className="field-error" role="alert">
          {error}
        </span>
      )}
    </div>
  )
}
