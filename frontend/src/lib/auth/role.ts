import type { UserRole } from '../../types/auth'

export function roleHomePath(role: UserRole): string {
  switch (role) {
    case 'buyer':
      return '/catalog'
    case 'seller':
      return '/seller'
    case 'ops':
      return '/ops'
  }
}

/** Rotulo do papel exibido na interface. */
export const ROLE_LABELS: Record<UserRole, string> = {
  buyer: 'Comprador',
  seller: 'Vendedor',
  ops: 'Operações',
}
