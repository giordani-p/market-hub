import type { UserRole } from '../../types/auth'

export function roleHomePath(role: UserRole): string {
  switch (role) {
    case 'buyer':
      return '/buyer'
    case 'seller':
      return '/seller'
    case 'ops':
      return '/ops'
  }
}
