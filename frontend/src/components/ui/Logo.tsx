import { ShoppingBag } from 'lucide-react'
import styles from './Logo.module.css'

type LogoSize = 'sm' | 'md'

const GLYPH_SIZE: Record<LogoSize, number> = { sm: 16, md: 22 }

/** Marca da aplicacao: simbolo mais wordmark, na mesma forma do favicon. */
export function Logo({ size = 'sm' }: { size?: LogoSize }) {
  return (
    <span className={`${styles.logo} ${styles[size]}`}>
      <span className={styles.mark} aria-hidden="true">
        <ShoppingBag size={GLYPH_SIZE[size]} />
      </span>
      Market Hub
    </span>
  )
}
