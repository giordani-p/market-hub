import { Menu, PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { Logo } from '../../components/ui/Logo'
import { Tooltip } from '../../components/ui/Tooltip'
import { NotificationBell } from '../../features/notifications/NotificationBell'
import { roleHomePath } from '../../lib/auth/role'
import { useAuth } from '../providers/auth-context'
import { GlobalSearch } from './GlobalSearch'
import { NAV_ITEMS, navOrientation, type NavItem } from './nav'
import { UserMenu } from './UserMenu'
import { useRouteFocus } from './useRouteFocus'
import styles from './AppLayout.module.css'

export function AppLayout() {
  const { user, logout } = useAuth()
  const { pathname } = useLocation()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  useRouteFocus()

  // Trocar de tela fecha o drawer: em telefone ele cobre o conteudo que a
  // navegacao acabou de pedir. Ajuste durante o render, nao em efeito --
  // assim o drawer nunca chega a ser pintado aberto na tela nova.
  const [drawerPathname, setDrawerPathname] = useState(pathname)
  if (drawerPathname !== pathname) {
    setDrawerPathname(pathname)
    setDrawerOpen(false)
  }

  useEffect(() => {
    if (!drawerOpen) {
      return
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setDrawerOpen(false)
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [drawerOpen])

  if (!user) {
    return null
  }

  const navItems = NAV_ITEMS[user.role]
  const orientation = navOrientation(user.role)

  return (
    <div className={styles.shell}>
      <a className={styles.skipLink} href="#main-content">
        Ir para o conteúdo
      </a>

      <header className={styles.header}>
        {orientation === 'sidebar' && (
          <button
            type="button"
            className={styles.drawerToggle}
            onClick={() => setDrawerOpen(true)}
            aria-label="Abrir navegação"
            aria-expanded={drawerOpen}
          >
            <Menu size={20} aria-hidden="true" />
          </button>
        )}

        <Link to={roleHomePath(user.role)} className={styles.brand}>
          <Logo />
        </Link>

        <GlobalSearch role={user.role} />

        <div className={styles.headerActions}>
          <NotificationBell role={user.role} />
          <UserMenu user={user} onLogout={logout} />
        </div>
      </header>

      {orientation === 'horizontal' && (
        <nav className={styles.topNav} aria-label="Navegação principal">
          {navItems.map((item) => (
            <TopNavLink key={item.to} item={item} />
          ))}
        </nav>
      )}

      <div className={styles.body}>
        {orientation === 'sidebar' && (
          <>
            {drawerOpen && (
              <div
                className={styles.drawerBackdrop}
                onClick={() => setDrawerOpen(false)}
                aria-hidden="true"
              />
            )}
            <nav
              className={[
                styles.sidebar,
                sidebarCollapsed ? styles.sidebarCollapsed : '',
                drawerOpen ? styles.sidebarOpen : '',
              ]
                .filter(Boolean)
                .join(' ')}
              aria-label="Navegação principal"
            >
              {navItems.map((item) => (
                <SidebarLink key={item.to} item={item} collapsed={sidebarCollapsed} />
              ))}
              <button
                type="button"
                className={styles.collapseButton}
                onClick={() => setSidebarCollapsed((value) => !value)}
                aria-label={sidebarCollapsed ? 'Expandir navegação' : 'Recolher navegação'}
              >
                {sidebarCollapsed ? (
                  <PanelLeftOpen size={18} aria-hidden="true" />
                ) : (
                  <>
                    <PanelLeftClose size={18} aria-hidden="true" />
                    Recolher
                  </>
                )}
              </button>
            </nav>
          </>
        )}

        <main className={styles.main} id="main-content" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}

function TopNavLink({ item }: { item: NavItem }) {
  const Icon = item.icon
  return (
    <NavLink
      to={item.to}
      end={item.end}
      className={({ isActive }) =>
        `${styles.topNavLink} ${isActive ? styles.topNavLinkActive : ''}`.trim()
      }
    >
      <Icon size={16} aria-hidden="true" />
      {item.label}
    </NavLink>
  )
}

function SidebarLink({ item, collapsed }: { item: NavItem; collapsed: boolean }) {
  const Icon = item.icon
  const link = (
    <NavLink
      to={item.to}
      end={item.end}
      className={({ isActive }) =>
        `${styles.sidebarLink} ${isActive ? styles.sidebarLinkActive : ''}`.trim()
      }
      aria-label={collapsed ? item.label : undefined}
    >
      <Icon size={18} aria-hidden="true" />
      {!collapsed && item.label}
    </NavLink>
  )

  // Recolhida, a sidebar mostra so icone: o rotulo precisa aparecer no
  // hover e no foco para o destino continuar identificavel.
  return collapsed ? (
    <Tooltip label={item.label} placement="right">
      {link}
    </Tooltip>
  ) : (
    link
  )
}
