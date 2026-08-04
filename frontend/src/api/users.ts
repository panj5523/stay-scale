import { apiClient } from './client'

export interface UserProfile { public_id: string; email: string; display_name: string }
export interface Favorite { listing_public_id: string; name: string; city: string; district: string; created_at: string }
interface LoginResult { access_token: string; expires_in: number; user: UserProfile }

export async function registerUser(email: string, password: string, displayName: string): Promise<LoginResult> {
  return (await apiClient.post<LoginResult>('/v1/users/auth/register', { email, password, display_name: displayName })).data
}
export async function loginUser(email: string, password: string): Promise<LoginResult> {
  return (await apiClient.post<LoginResult>('/v1/users/auth/login', { email, password })).data
}
export async function getUserProfile(): Promise<UserProfile> { return (await apiClient.get<UserProfile>('/v1/users/me')).data }
export async function getUserFavorites(): Promise<Favorite[]> { return (await apiClient.get<Favorite[]>('/v1/users/me/favorites')).data }
export async function addUserFavorite(listingId: string): Promise<Favorite> {
  return (await apiClient.put<Favorite>(`/v1/users/me/favorites/${listingId}`)).data
}
export async function removeUserFavorite(listingId: string): Promise<void> { await apiClient.delete(`/v1/users/me/favorites/${listingId}`) }
export async function getRecommendationHistory(): Promise<Array<{ session_id: string; request: { city: string; check_in: string; check_out: string }; results: unknown[] }>> {
  return (await apiClient.get('/v1/recommendations/history')).data
}
export interface TravelPlanHistoryItem {
  plan_id: string
  recommendation_session_id: string
  status: 'draft'
  city: string
  check_in: string
  check_out: string
  guests: number
  provider: string
  model: string
  summary: string
  days: Array<{ date: string; title: string; items: Array<{ time_label: string; activity: string; reason: string; note: string }> }>
  warnings: string[]
  created_at: string
}
export async function getTravelPlanHistory(): Promise<TravelPlanHistoryItem[]> {
  return (await apiClient.get('/v1/users/me/travel-plans')).data
}
