import type { ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Spinner } from '../../components/feedback/Spinner'
import { ProductDetailPage } from '../../features/catalog/ProductDetailPage'
import { ProductListPage } from '../../features/catalog/ProductListPage'
import { LoginPage } from '../../features/auth/LoginPage'
import { OrderDetailPage } from '../../features/orders/OrderDetailPage'
import { OrdersListPage } from '../../features/orders/OrdersListPage'
import { roleHomePath } from '../../lib/auth/role'
import { AppLayout } from '../layout/AppLayout'
import { NotFoundPage } from '../layout/NotFoundPage'
import { RoleHomePage } from '../layout/RoleHomePage'
import { useAuth } from '../providers/auth-context'

function ProtectedArea({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  if (status === 'checking') {
    return <Spinner label="Carregando sessão..." />
  }
  if (status === 'unauthenticated') {
    return <Navigate to="/login" replace />
  }
  return children
}

function PublicOnlyRoute({ children }: { children: ReactNode }) {
  const { status, user } = useAuth()
  if (status === 'checking') {
    return <Spinner label="Carregando sessão..." />
  }
  if (status === 'authenticated' && user) {
    return <Navigate to={roleHomePath(user.role)} replace />
  }
  return children
}

function HomeRedirect() {
  const { user } = useAuth()
  if (!user) {
    return null
  }
  return <Navigate to={roleHomePath(user.role)} replace />
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={
            <PublicOnlyRoute>
              <LoginPage />
            </PublicOnlyRoute>
          }
        />
        <Route
          element={
            <ProtectedArea>
              <AppLayout />
            </ProtectedArea>
          }
        >
          <Route path="/" element={<HomeRedirect />} />
          <Route path="/buyer/catalog" element={<ProductListPage />} />
          <Route path="/buyer/catalog/:productId" element={<ProductDetailPage />} />
          <Route path="/buyer/orders" element={<OrdersListPage />} />
          <Route path="/buyer/orders/:orderId" element={<OrderDetailPage />} />
          <Route path="/seller" element={<RoleHomePage role="seller" />} />
          <Route path="/ops" element={<RoleHomePage role="ops" />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}
