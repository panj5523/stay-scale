import { apiClient } from './client'
import type { RecommendationParams, RecommendationResponse } from '../types/recommendations'

export async function createRecommendation(
  params: RecommendationParams,
): Promise<RecommendationResponse> {
  const response = await apiClient.post<RecommendationResponse>('/v1/recommendations', {
    city: params.city,
    check_in: params.checkIn,
    check_out: params.checkOut,
    guests: params.guests,
    budget_total: params.budgetTotal,
    preferred_facilities: params.preferredFacilities,
    preferred_districts: params.preferredDistricts,
    travel_style: params.travelStyle,
    top_k: params.topK,
  })
  return response.data
}

export async function getRecommendation(sessionId: string): Promise<RecommendationResponse> {
  const response = await apiClient.get<RecommendationResponse>(`/v1/recommendations/${sessionId}`)
  return response.data
}
