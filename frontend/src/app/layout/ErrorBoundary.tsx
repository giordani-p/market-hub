import { Component, type ReactNode } from 'react'
import { ErrorState } from '../../components/feedback/ErrorState'

interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        <ErrorState
          message="Algo deu errado. Recarregue a página."
          onRetry={() => window.location.reload()}
        />
      )
    }
    return this.props.children
  }
}
