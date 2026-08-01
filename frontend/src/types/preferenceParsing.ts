import type { TravelStyle } from './recommendations'

export type RiskAversion = 'low' | 'medium' | 'high'

export interface ParsedPreferences {
  city: string | null
  check_in: string | null
  check_out: string | null
  guests: number | null
  budget_total: string | null
  preferred_facilities: string[]
  preferred_districts: string[]
  travel_style: TravelStyle | null
  risk_aversion: RiskAversion
}

export interface ExtractionEvidence {
  field: string
  matched_text: string
  normalized_value: string
}

export interface PreferenceParseResponse {
  session_id: string
  status: 'needs_confirmation' | 'confirmed'
  parser_name: string
  parser_version: string
  confidence: string
  original_text: string
  draft: ParsedPreferences
  evidence: ExtractionEvidence[]
  missing_fields: string[]
  warnings: string[]
  created_at: string
  confirmed_at: string | null
}
