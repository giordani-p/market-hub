import { EmptyState } from '../../components/feedback/EmptyState'
import type { UserRole } from '../../types/auth'

const MESSAGES: Record<UserRole, string> = {
  buyer: 'A jornada de Catalog e Purchase chega na próxima fase.',
  seller: 'A listagem de Orders chega na próxima fase.',
  ops: 'A fila de Ops chega em uma fase futura.',
}

export function RoleHomePage({ role }: { role: UserRole }) {
  return <EmptyState title="Em construção" description={MESSAGES[role]} />
}
