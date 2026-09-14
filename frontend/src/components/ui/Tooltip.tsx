import { useId, useState, type ReactNode } from 'react'
import styles from './Tooltip.module.css'

interface TooltipProps {
  label: string
  placement?: 'top' | 'right'
  children: ReactNode
}

/** Rotulo visivel para icone isolado. Aparece no hover e tambem no foco. */
export function Tooltip({ label, placement = 'top', children }: TooltipProps) {
  const id = useId()
  const [visible, setVisible] = useState(false)

  return (
    <span
      className={styles.wrapper}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      <span aria-describedby={id}>{children}</span>
      {visible && (
        <span
          className={`${styles.bubble} ${placement === 'right' ? styles.right : ''}`.trim()}
          role="tooltip"
          id={id}
        >
          {label}
        </span>
      )}
    </span>
  )
}
