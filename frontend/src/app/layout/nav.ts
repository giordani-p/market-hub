import type { UserRole } from '../../types/auth'

interface NavItem {
  label: string
  to: string
  /** true no Inicio para nao marcar ativo em rotas aninhadas. */
  end?: boolean
}

export const NAV_ITEMS: Record<UserRole, NavItem[]> = {
  buyer: [
    { label: 'Início', to: '/buyer', end: true },
    { label: 'Catálogo', to: '/catalog' },
    { label: 'Meus pedidos', to: '/buyer/orders' },
  ],
  seller: [
    { label: 'Início', to: '/seller', end: true },
    { label: 'Catálogo', to: '/catalog' },
    { label: 'Pedidos', to: '/seller/orders' },
    { label: 'Minhas ofertas', to: '/seller/offers' },
  ],
  ops: [
    { label: 'Início', to: '/ops', end: true },
    { label: 'Catálogo', to: '/catalog' },
    { label: 'Fila', to: '/ops/queue' },
    { label: 'Pedidos', to: '/ops/order-items' },
  ],
}
