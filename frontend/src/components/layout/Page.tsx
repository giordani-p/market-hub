import type { ReactNode } from 'react'
import styles from './Page.module.css'

interface PageProps {
  children: ReactNode
  width?: 'narrow' | 'default' | 'wide'
}

export function Page({ children, width = 'default' }: PageProps) {
  const widthClass = width === 'default' ? '' : styles[width]
  return <div className={`${styles.page} ${widthClass}`.trim()}>{children}</div>
}
