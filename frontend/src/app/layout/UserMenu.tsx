import { ChevronDown, LogOut } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Avatar } from '../../components/ui/Avatar'
import { Button } from '../../components/ui/Button'
import type { AuthUser } from '../../types/auth'
import { ROLE_LABELS } from '../../lib/auth/role'
import styles from './UserMenu.module.css'

interface UserMenuProps {
  user: AuthUser
  onLogout: () => void
}

/** Agrupa identidade e saida, que antes ocupavam o header soltos. */
export function UserMenu({ user, onLogout }: UserMenuProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (!open) {
      return
    }
    function handlePointerDown(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handlePointerDown)
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('mousedown', handlePointerDown)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [open])

  return (
    <div className={styles.userMenu} ref={containerRef}>
      <button
        type="button"
        className={styles.trigger}
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-label={`Conta de ${user.name}`}
      >
        <Avatar name={user.name} />
        <span className={styles.triggerName}>{user.name}</span>
        <ChevronDown size={14} className={styles.chevron} aria-hidden="true" />
      </button>

      {open && (
        <div className={styles.dropdown}>
          <div className={styles.identity}>
            <span className={styles.name}>{user.name}</span>
            <span className={styles.role}>{ROLE_LABELS[user.role]}</span>
          </div>
          <Button type="button" variant="secondary" size="sm" fullWidth onClick={onLogout}>
            <LogOut size={16} aria-hidden="true" />
            Sair
          </Button>
        </div>
      )}
    </div>
  )
}
