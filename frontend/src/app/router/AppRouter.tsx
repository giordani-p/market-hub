import type { ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useParams } from 'react-router-dom'
import { Spinner } from '../../components/feedback/Spinner'
import { ProductDetailPage } from '../../features/catalog/ProductDetailPage'
import { ProductListPage } from '../../features/catalog/ProductListPage'
import { LoginPage } from '../../features/auth/LoginPage'
import { DashboardPage } from '../../features/dashboard/DashboardPage'
import { BuyerOrderItemDetailPage } from '../../features/orders/BuyerOrderItemDetailPage'
import { OrderDetailPage } from '../../features/orders/OrderDetailPage'
import { OrdersListPage } from '../../features/orders/OrdersListPage'
import { OpsConversationDetailPage } from '../../features/ops/OpsConversationDetailPage'
import { OpsOrderItemDetailPage } from '../../features/ops/OpsOrderItemDetailPage'
import { OpsOrderItemsListPage } from '../../features/ops/OpsOrderItemsListPage'
import { OpsQueuePage } from '../../features/ops/OpsQueuePage'
import { SellerOfferDetailPage } from '../../features/seller-offers/SellerOfferDetailPage'
import { SellerOfferNewPage } from '../../features/seller-offers/SellerOfferNewPage'
import { SellerOffersListPage } from '../../features/seller-offers/SellerOffersListPage'
import { SellerOrderItemDetailPage } from '../../features/seller-orders/SellerOrderItemDetailPage'
import { SellerOrdersListPage } from '../../features/seller-orders/SellerOrdersListPage'
import { roleHomePath } from '../../lib/auth/role'
import { AppLayout } from '../layout/AppLayout'
import { NotFoundPage } from '../layout/NotFoundPage'
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
          <Route path="/buyer" element={<DashboardPage />} />
          <Route path="/seller" element={<DashboardPage />} />
          <Route path="/ops" element={<DashboardPage />} />
          <Route path="/catalog" element={<ProductListPage />} />
          <Route path="/catalog/:productId" element={<ProductDetailPage />} />
          <Route path="/buyer/catalog" element={<Navigate to="/catalog" replace />} />
          <Route path="/buyer/catalog/:productId" element={<BuyerCatalogRedirect />} />
          <Route path="/buyer/orders" element={<OrdersListPage />} />
          <Route path="/buyer/orders/:orderId" element={<OrderDetailPage />} />
          <Route
            path="/buyer/orders/:orderId/items/:itemId"
            element={<BuyerOrderItemDetailPage />}
          />
          <Route path="/seller/orders" element={<SellerOrdersListPage />} />
          <Route path="/seller/orders/:itemId" element={<SellerOrderItemDetailPage />} />
          <Route path="/seller/offers" element={<SellerOffersListPage />} />
          <Route path="/seller/offers/new" element={<SellerOfferNewPage />} />
          <Route path="/seller/offers/:offerId" element={<SellerOfferDetailPage />} />
          <Route path="/ops/queue" element={<OpsQueuePage />} />
          <Route
            path="/ops/conversations/:conversationId"
            element={<OpsConversationDetailPage />}
          />
          <Route path="/ops/order-items" element={<OpsOrderItemsListPage />} />
          <Route path="/ops/order-items/:itemId" element={<OpsOrderItemDetailPage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}

function BuyerCatalogRedirect() {
  const { productId } = useParams<{ productId: string }>()
  return <Navigate to={`/catalog/${productId}`} replace />
}
