import styles from './Avatar.module.css'

/** Iniciais do nome: primeira letra do primeiro e do ultimo termo. */
function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) {
    return '?'
  }
  if (parts.length === 1) {
    return parts[0].slice(0, 2)
  }
  return `${parts[0][0]}${parts[parts.length - 1][0]}`
}

export function Avatar({ name }: { name: string }) {
  return (
    <span className={styles.avatar} aria-hidden="true">
      {initials(name)}
    </span>
  )
}
