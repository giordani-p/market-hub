import type { UserRole } from '../../types/auth'

export function roleHomePath(role: UserRole): string {
  switch (role) {
    case 'buyer':
      return '/buyer/catalog'
    case 'seller':
      return '/seller/orders'
    case 'ops':
      return '/ops'
  }
}
