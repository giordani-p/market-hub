import { AppRouter } from './app/router/AppRouter'
import { ErrorBoundary } from './app/layout/ErrorBoundary'
import { AuthProvider } from './app/providers/AuthProvider'

export function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </ErrorBoundary>
  )
}
