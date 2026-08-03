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

export interface ArchiveResponse {
  archive_id: string
  file_name: string
  file_path: string
  sha256: string
  counts: Record<string, number>
  generated_at: string
  deletion_performed: boolean
  warnings: string[]
}

export interface ArchiveFileInfo {
  archive_id: string
  file_name: string
  size_bytes: number
  created_at: string
  sha256: string | null
  integrity_status: 'not_checked' | 'valid' | 'invalid'
}

export interface RestorePreview {
  archive_id: string
  file_name: string
  integrity_status: string
  manifest_found: boolean
  tables_found: string[]
  missing_tables: string[]
  record_counts: Record<string, number>
  total_records: number
  restore_performed: boolean
  warnings: string[]
}

export interface RestorePlan {
  archive_id: string
  execution_order: string[]
  tables: Array<{
    table: string
    archive_records: number
    insert_candidates: number
    existing_conflicts: number
    invalid_records: number
  }>
  total_insert_candidates: number
  total_conflicts: number
  can_restore_safely: boolean
  restore_performed: boolean
  blockers: string[]
}

export interface RestoreRequest {
  public_id: string
  archive_id: string
  requested_by: number
  reviewed_by: number | null
  executed_by: number | null
  executed_at: string | null
  execution_summary: {
    archive_sha256: string
    inserted_counts: Record<string, number>
    total_inserted: number
    overwrite_performed: boolean
    deletion_performed: boolean
  } | null
  status: 'pending' | 'approved' | 'rejected'
  plan_snapshot: RestorePlan
  decision_reason: string | null
  created_at: string
  updated_at: string
}

export interface RestoreExecutionReadiness {
  request_public_id: string
  archive_id: string
  approved: boolean
  archive_integrity_valid: boolean
  archive_unchanged: boolean
  plan_unchanged: boolean
  no_conflicts: boolean
  ready_to_execute: boolean
  execution_performed: boolean
  blockers: string[]
}

export interface RestoreExecuteResult {
  request_public_id: string
  archive_id: string
  status: string
  inserted_counts: Record<string, number>
  total_inserted: number
  overwrite_performed: boolean
  deletion_performed: boolean
}
