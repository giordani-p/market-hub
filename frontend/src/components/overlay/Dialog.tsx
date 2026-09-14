import { useEffect, useRef, type ReactNode } from 'react'
import styles from './Dialog.module.css'

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

interface DialogProps {
  open: boolean
  title: string
  description?: string
  onClose: () => void
  children: ReactNode
}

/**
 * Confirmacao de acao irreversivel.
 *
 * Substitui o padrao anterior de confirmacao inline, que nao prendia foco,
 * nao fechava no Escape e deixava o resto da tela operavel enquanto pedia
 * uma decisao.
 */
export function Dialog({ open, title, description, onClose, children }: DialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const previouslyFocused = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (!open) {
      return
    }
    previouslyFocused.current = document.activeElement as HTMLElement | null
    const node = dialogRef.current
    node?.querySelector<HTMLElement>(FOCUSABLE)?.focus()

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose()
        return
      }
      if (event.key !== 'Tab' || !node) {
        return
      }
      // Foco preso: Tab no ultimo elemento volta ao primeiro, e vice-versa.
      const focusable = Array.from(node.querySelectorAll<HTMLElement>(FOCUSABLE))
      if (focusable.length === 0) {
        return
      }
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      previouslyFocused.current?.focus()
    }
  }, [open, onClose])

  if (!open) {
    return null
  }

  const titleId = 'dialog-title'
  const descriptionId = description ? 'dialog-description' : undefined

  return (
    <div
      className={styles.backdrop}
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          onClose()
        }
      }}
    >
      <div
        ref={dialogRef}
        className={styles.dialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
      >
        <h2 id={titleId}>{title}</h2>
        {description && (
          <p className={styles.description} id={descriptionId}>
            {description}
          </p>
        )}
        {children}
      </div>
    </div>
  )
}

export function DialogActions({ children }: { children: ReactNode }) {
  return <div className={styles.actions}>{children}</div>
}
