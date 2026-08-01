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
  tradeoffs?: string[]
  risk_notes?: string[]
  natural_explanation?: string | null
  explanation_source?: string | null
}

export interface RecommendationAdjustmentResponse {
  original_session_id: string
  new_session_id: string
  feedback: string
  applied_changes: Record<string, unknown>
  warnings: string[]
  recommendation: RecommendationResponse
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
  explanation_status?: 'not_requested' | 'generated' | 'fallback'
  explanation_provider?: string | null
  explanation_model?: string | null
  explanation_warning?: string | null
}

export interface TravelPlanItem {
  time_label: string
  activity: string
  reason: string
  note: string
}

export interface TravelPlanDay {
  date: string
  title: string
  items: TravelPlanItem[]
}

export interface TravelPlanResponse {
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
  days: TravelPlanDay[]
  warnings: string[]
  created_at: string
}
