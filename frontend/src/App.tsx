import { AppRouter } from './app/router/AppRouter'
import { ErrorBoundary } from './app/layout/ErrorBoundary'
import { AuthProvider } from './app/providers/AuthProvider'
import { ToastProvider } from './components/overlay/ToastProvider'

export function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </ToastProvider>
    </ErrorBoundary>
  )
}
