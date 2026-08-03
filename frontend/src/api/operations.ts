import { apiClient } from './client'
import type { OperationsDashboard } from '../types/operations'
import type { DataRetentionReport } from '../types/operations'
import type { ArchiveResponse } from '../types/operations'
import type { ArchiveFileInfo } from '../types/operations'
import type { RestorePreview } from '../types/operations'
import type { RestorePlan } from '../types/operations'
import type { RestoreRequest } from '../types/operations'
import type { RestoreExecutionReadiness } from '../types/operations'
import type { RestoreExecuteResult } from '../types/operations'

export async function getOperationsDashboard(): Promise<OperationsDashboard> {
  const response = await apiClient.get<OperationsDashboard>('/v1/management/dashboard')
  return response.data
}

export async function getDataRetentionReport(): Promise<DataRetentionReport> {
  const response = await apiClient.get<DataRetentionReport>('/v1/management/data-retention/report')
  return response.data
}

export async function createDataRetentionArchive(): Promise<ArchiveResponse> {
  const response = await apiClient.post<ArchiveResponse>('/v1/management/data-retention/archive', { confirm: true })
  return response.data
}

export async function listDataRetentionArchives(): Promise<ArchiveFileInfo[]> {
  const response = await apiClient.get<{ archives: ArchiveFileInfo[] }>('/v1/management/data-retention/archives')
  return response.data.archives
}

export async function verifyDataRetentionArchive(archiveId: string): Promise<ArchiveFileInfo> {
  const response = await apiClient.post<ArchiveFileInfo>(`/v1/management/data-retention/archives/${archiveId}/verify`)
  return response.data
}

export async function downloadDataRetentionArchive(archive: ArchiveFileInfo): Promise<void> {
  const response = await apiClient.get(`/v1/management/data-retention/archives/${archive.archive_id}/download`, { responseType: 'blob' })
  const url = URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  link.download = archive.file_name
  link.click()
  URL.revokeObjectURL(url)
}

export async function previewDataRetentionRestore(archiveId: string): Promise<RestorePreview> {
  const response = await apiClient.get<RestorePreview>(`/v1/management/data-retention/archives/${archiveId}/restore-preview`)
  return response.data
}

export async function planDataRetentionRestore(archiveId: string): Promise<RestorePlan> {
  const response = await apiClient.get<RestorePlan>(`/v1/management/data-retention/archives/${archiveId}/restore-plan`)
  return response.data
}

export async function listRestoreRequests(): Promise<RestoreRequest[]> {
  const response = await apiClient.get<RestoreRequest[]>('/v1/management/data-retention/restore-requests')
  return response.data
}

export async function decideRestoreRequest(publicId: string, action: 'approved' | 'rejected', reason: string): Promise<RestoreRequest> {
  const response = await apiClient.patch<RestoreRequest>(`/v1/management/data-retention/restore-requests/${publicId}`, { action, reason })
  return response.data
}

export async function getRestoreExecutionReadiness(publicId: string): Promise<RestoreExecutionReadiness> {
  const response = await apiClient.get<RestoreExecutionReadiness>(`/v1/management/data-retention/restore-requests/${publicId}/execution-readiness`)
  return response.data
}

export async function executeRestoreRequest(publicId: string, confirmation: string): Promise<RestoreExecuteResult> {
  const response = await apiClient.post<RestoreExecuteResult>(`/v1/management/data-retention/restore-requests/${publicId}/execute`, { confirmation })
  return response.data
}
