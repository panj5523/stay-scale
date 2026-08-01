export type TravelStyle = 'value' | 'comfort' | 'scenery' | 'family'

export interface RecommendationParams {
  city: string
  checkIn: string
  checkOut: string
  guests: number
  budgetTotal?: number
  preferredFacilities: string[]
  preferredDistricts: string[]
  travelStyle: TravelStyle
  topK: number
}

export interface ScoreBreakdown {
  price: string
  rating: string
  facilities: string
  platform_coverage: string
  location: string
}

export interface RecommendationItem {
  rank: number
  listing_public_id: string
  listing_name: string
  district: string
  total_amount: string
  currency: string
  best_rating: string | null
  platform_count: number
  total_score: string
  score_breakdown: ScoreBreakdown
  reasons: string[]
}

export interface RecommendationRequestSnapshot {
  city: string
  check_in: string
  check_out: string
  guests: number
  budget_total: string | null
  preferred_facilities: string[]
  preferred_districts: string[]
  travel_style: TravelStyle
  top_k: number
}

export interface RecommendationResponse {
  session_id: string
  status: 'completed' | 'no_candidates'
  algorithm_version: string
  request: RecommendationRequestSnapshot
  results: RecommendationItem[]
  generated_at: string
}
