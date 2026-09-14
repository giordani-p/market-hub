import { ErrorState } from '../../components/feedback/ErrorState'
import { SkeletonList } from '../../components/ui/Skeleton'
import { Page } from '../../components/layout/Page'
import { useAsync } from '../../lib/utils/useAsync'
import { fetchDashboard } from './api'
import { BuyerDashboardView } from './BuyerDashboardView'
import { OpsDashboardView } from './OpsDashboardView'
import { SellerDashboardView } from './SellerDashboardView'

export function DashboardPage() {
  const state = useAsync(fetchDashboard, [])

  if (state.status === 'loading') {
    return (
      <Page>
        <SkeletonList count={3} variant="stat" label="Carregando início..." />
      </Page>
    )
  }
  if (state.status === 'error') {
    return (
      <Page>
        <ErrorState message={state.error} onRetry={state.retry} />
      </Page>
    )
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
