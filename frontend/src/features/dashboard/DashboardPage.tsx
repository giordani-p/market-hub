import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { useAsync } from '../../lib/utils/useAsync'
import { fetchDashboard } from './api'
import { BuyerDashboardView } from './BuyerDashboardView'
import { OpsDashboardView } from './OpsDashboardView'
import { SellerDashboardView } from './SellerDashboardView'

export function DashboardPage() {
  const state = useAsync(fetchDashboard, [])

  if (state.status === 'loading') {
    return <Spinner label="Carregando início..." />
  }
  if (state.status === 'error') {
    return <ErrorState message={state.error} onRetry={state.retry} />
  }

  const data = state.data
  if (data.role === 'seller') {
    return <SellerDashboardView data={data} />
  }
  if (data.role === 'buyer') {
    return <BuyerDashboardView data={data} />
  }
  return <OpsDashboardView data={data} />
}
