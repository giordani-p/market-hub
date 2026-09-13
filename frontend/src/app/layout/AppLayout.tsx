import { Outlet } from 'react-router-dom'
import { Button } from '../../components/ui/Button'
import { useAuth } from '../providers/auth-context'
import { NAV_ITEMS } from './nav'

export function AppLayout() {
  const { user, logout } = useAuth()
  const navItems = user ? NAV_ITEMS[user.role] : []

  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-title">Market Hub</span>
        <div className="app-header-user">
          <span className="app-notifications" aria-hidden="true" title="Notificações (em breve)">
            🔔
          </span>
          <span>{user?.name}</span>
          <Button variant="secondary" onClick={logout}>
            Sair
          </Button>
        </div>
      </header>
      <div className="app-body">
        <nav className="app-nav" aria-label="Navegação principal">
          {navItems.map((item) => (
            <span key={item.label} className="app-nav-item" aria-disabled="true" title="Em breve">
              {item.label}
            </span>
          ))}
        </nav>
        <main className="app-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
