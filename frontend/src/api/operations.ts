import { apiClient } from './client'
import type { OperationsDashboard } from '../types/operations'

export async function getOperationsDashboard(): Promise<OperationsDashboard> {
  const response = await apiClient.get<OperationsDashboard>('/v1/management/dashboard')
  return response.data
}
