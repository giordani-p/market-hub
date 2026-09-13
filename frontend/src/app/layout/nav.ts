import type { UserRole } from '../../types/auth'

interface NavItem {
  label: string
}

/** Itens desabilitados na F0: as features correspondentes ainda não existem. */
export const NAV_ITEMS: Record<UserRole, NavItem[]> = {
  buyer: [{ label: 'Catalog' }, { label: 'My Orders' }],
  seller: [{ label: 'Orders' }],
  ops: [{ label: 'Operations' }, { label: 'Queue' }],
}
