import { Home, LifeBuoy, Package, ShoppingBag, Store, type LucideIcon } from 'lucide-react'
import type { UserRole } from '../../types/auth'

export interface NavItem {
  label: string
  to: string
  icon: LucideIcon
  /** true no Inicio para nao marcar ativo em rotas aninhadas. */
  end?: boolean
}

export const NAV_ITEMS: Record<UserRole, NavItem[]> = {
  buyer: [
    { label: 'Início', to: '/buyer', icon: Home, end: true },
    { label: 'Catálogo', to: '/catalog', icon: Store },
    { label: 'Meus pedidos', to: '/buyer/orders', icon: Package },
  ],
  seller: [
    { label: 'Início', to: '/seller', icon: Home, end: true },
    { label: 'Pedidos', to: '/seller/orders', icon: Package },
    { label: 'Minhas ofertas', to: '/seller/offers', icon: ShoppingBag },
    { label: 'Catálogo', to: '/catalog', icon: Store },
  ],
  ops: [
    { label: 'Início', to: '/ops', icon: Home, end: true },
    { label: 'Fila de atendimento', to: '/ops/queue', icon: LifeBuoy },
    { label: 'Pedidos', to: '/ops/order-items', icon: Package },
    { label: 'Catálogo', to: '/catalog', icon: Store },
  ],
}

/**
 * Buyer navega na horizontal, como vitrine; Seller e Ops usam sidebar,
 * porque a jornada deles e operacional e a lista de destinos cresce.
 */
export function navOrientation(role: UserRole): 'horizontal' | 'sidebar' {
  return role === 'buyer' ? 'horizontal' : 'sidebar'
}
