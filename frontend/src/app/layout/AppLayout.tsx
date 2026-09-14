import { NavLink, Outlet } from 'react-router-dom'
import { Button } from '../../components/ui/Button'
import { NotificationBell } from '../../features/notifications/NotificationBell'
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
          {user && <NotificationBell role={user.role} />}
          <span>{user?.name}</span>
          <Button variant="secondary" onClick={logout}>
            Sair
          </Button>
        </div>
      </header>
      <div className="app-body">
        <nav className="app-nav" aria-label="Navegação principal">
          {navItems.map((item) =>
            item.to ? (
              <NavLink
                key={item.label}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `app-nav-item app-nav-link${isActive ? ' app-nav-link-active' : ''}`
                }
              >
                {item.label}
              </NavLink>
            ) : (
              <span key={item.label} className="app-nav-item" aria-disabled="true" title="Em breve">
                {item.label}
              </span>
            ),
          )}
        </nav>
        <main className="app-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
