import type { ParsedPreferences } from '../types/preferenceParsing'

const TRANSFER_KEY = 'stay_scale_ai_recommendation_draft'

export function saveAIRecommendationDraft(draft: ParsedPreferences): void {
  sessionStorage.setItem(TRANSFER_KEY, JSON.stringify(draft))
}

export function consumeAIRecommendationDraft(): ParsedPreferences | null {
  const stored = sessionStorage.getItem(TRANSFER_KEY)
  sessionStorage.removeItem(TRANSFER_KEY)
  if (!stored) return null
  try {
    const parsed: unknown = JSON.parse(stored)
    return parsed && typeof parsed === 'object' ? parsed as ParsedPreferences : null
  } catch {
    return null
  }
}
