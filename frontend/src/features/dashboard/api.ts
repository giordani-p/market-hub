import { apiRequest } from '../../lib/api/client'
import type { DashboardResponse } from '../../types/dashboard'

export function fetchDashboard(): Promise<DashboardResponse> {
  return apiRequest<DashboardResponse>('/dashboard')
}
