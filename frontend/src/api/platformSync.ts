import { apiClient } from './client'

export interface SyncSource {
  public_id: string
  platform_code: string
  platform_name: string
  connector_type: 'fixture' | 'authorized_api'
  source_label: string
  interval_minutes: number
  status: string
  is_enabled: boolean
  last_run_at: string | null
  last_success_at: string | null
  last_error: string | null
  next_run_at: string | null
}

export async function getSyncSources(): Promise<SyncSource[]> {
  return (await apiClient.get('/v1/management/platform-sync/sources')).data
}
export async function configureSyncSource(platformCode: string, sourceLabel: string, intervalMinutes: number, isEnabled: boolean): Promise<SyncSource> {
  return (await apiClient.put(`/v1/management/platform-sync/sources/${platformCode}`, { connector_type: 'fixture', source_label: sourceLabel, interval_minutes: intervalMinutes, is_enabled: isEnabled })).data
}
export async function runSyncSource(platformCode: string): Promise<void> {
  await apiClient.post(`/v1/management/platform-sync/sources/${platformCode}/run`)
}
