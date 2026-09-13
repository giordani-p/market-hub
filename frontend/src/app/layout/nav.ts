import type { UserRole } from '../../types/auth'

interface NavItem {
  label: string
  /** Ausente enquanto a feature correspondente nao existe (item so exibido, sem link). */
  to?: string
}

export const NAV_ITEMS: Record<UserRole, NavItem[]> = {
  buyer: [
    { label: 'Catalog', to: '/buyer/catalog' },
    { label: 'My Orders', to: '/buyer/orders' },
  ],
  seller: [{ label: 'Orders' }],
  ops: [{ label: 'Operations' }, { label: 'Queue' }],
}
