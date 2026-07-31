import { apiClient } from './client'
import type { ReadinessResponse } from '../types/health'

export async function getReadiness(): Promise<ReadinessResponse> {
  const response = await apiClient.get<ReadinessResponse>('/v1/health/ready', {
    validateStatus: (status) => status === 200 || status === 503,
  })

  return response.data
}
