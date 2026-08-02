import { apiClient } from './client'
import type {
  ReviewDecision,
  ReviewDecisionResponse,
  ReviewQueueResponse,
  ReviewStatus,
} from '../types/managementReview'

export async function getReviewTasks(
  status: ReviewStatus | 'all' = 'pending',
): Promise<ReviewQueueResponse> {
  const response = await apiClient.get<ReviewQueueResponse>('/v1/management/reviews', {
    params: { status, page: 1, page_size: 50 },
  })
  return response.data
}

export async function decideReviewTask(
  recordId: number,
  decision: ReviewDecision,
): Promise<ReviewDecisionResponse> {
  const response = await apiClient.post<ReviewDecisionResponse>(
    `/v1/management/reviews/${recordId}/decision`,
    {
      action: decision.action,
      reviewer_name: decision.reviewerName,
      reason: decision.reason,
      target_canonical_public_id: decision.targetCanonicalPublicId,
    },
  )
  return response.data
}
