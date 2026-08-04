import { apiClient } from './client'
import type { ParsedPreferences } from '../types/preferenceParsing'

export interface ConversationMessage { role: string; content: string; structured_result: ParsedPreferences | null; created_at: string }
export interface Conversation { public_id: string; title: string; status: string; created_at: string; messages: ConversationMessage[] }
export async function createConversation(title = '旅行需求对话'): Promise<Conversation> { return (await apiClient.post('/v1/users/ai/conversations', { title })).data }
export async function sendConversationMessage(id: string, content: string): Promise<Conversation> { return (await apiClient.post(`/v1/users/ai/conversations/${id}/messages`, { content })).data }
