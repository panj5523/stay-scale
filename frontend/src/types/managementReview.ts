export type ReviewStatus = 'pending' | 'approved' | 'rejected'

export interface ReviewCandidate {
  public_id: string
  name: string
  city: string
  district: string
  address: string
}

export interface ReviewTask {
  record_id: number
  batch_id: number
  platform_code: string
  external_id: string
  listing_name: string
  review_status: ReviewStatus | 'not_required'
  match_method: string
  match_score: string
  match_decision: string
  evidence: Record<string, unknown>
  normalized_payload: Record<string, unknown>
  candidate: ReviewCandidate | null
  created_at: string
  reviewed_at: string | null
}

export interface ReviewQueueResponse {
  items: ReviewTask[]
  total: number
  page: number
  page_size: number
}

export interface ReviewDecision {
  action: 'approve' | 'reject'
  reviewerName: string
  reason: string
  targetCanonicalPublicId?: string
}

export interface ReviewDecisionResponse {
  audit_id: string
  record_id: number
  review_status: 'approved' | 'rejected'
  target_canonical_public_id: string | null
  reviewer_name: string
  reason: string
  reviewed_at: string
}
