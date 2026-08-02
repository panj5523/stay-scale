import { apiClient } from './client'
import type { OperationsDashboard } from '../types/operations'
import type { DataRetentionReport } from '../types/operations'

export async function getOperationsDashboard(): Promise<OperationsDashboard> {
  const response = await apiClient.get<OperationsDashboard>('/v1/management/dashboard')
  return response.data
}

export async function getDataRetentionReport(): Promise<DataRetentionReport> {
  const response = await apiClient.get<DataRetentionReport>('/v1/management/data-retention/report')
  return response.data
}
