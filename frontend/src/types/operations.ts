export interface OperationsDashboard {
  generated_at: string
  review_queue: { pending: number; approved: number; rejected: number }
  ingestion: {
    batches_24h: number
    completed_batches_24h: number
    failed_batches_24h: number
    records_24h: number
  }
  listing_quality: {
    active_canonical_listings: number
    active_platform_listings: number
    platform_coverage: Array<{
      platform_code: string
      platform_name: string
      active_listing_count: number
    }>
  }
  ai_usage: {
    preference_parse_count: number
    recommendation_explanation_count: number
    travel_plan_count: number
    review_analysis_count: number
    total_tokens: number
  }
  warnings: string[]
  data_retention?: DataRetentionReport
}

export interface DataRetentionReport {
  generated_at: string
  total_eligible_count: number
  archive_recommended: boolean
  warnings: string[]
  categories: Array<{
    key: string
    label: string
    table: string
    retention_days: number
    cutoff_date: string
    total_count: number
    eligible_count: number
    archive_recommended: boolean
  }>
}
