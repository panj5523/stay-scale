import { apiClient } from './client'
import type {
  ParsedPreferences,
  PreferenceParseResponse,
} from '../types/preferenceParsing'

export async function parsePreferences(text: string): Promise<PreferenceParseResponse> {
  const response = await apiClient.post<PreferenceParseResponse>('/v1/preference-parses', { text })
  return response.data
}

export async function confirmPreferenceParse(
  sessionId: string,
  preferences: ParsedPreferences,
): Promise<PreferenceParseResponse> {
  const response = await apiClient.patch<PreferenceParseResponse>(
    `/v1/preference-parses/${sessionId}/confirm`,
    { preferences },
  )
  return response.data
}
