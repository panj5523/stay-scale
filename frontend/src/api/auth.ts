import { apiClient } from './client'
import type { AdminLoginResponse, AdminUser } from '../types/auth'

export async function loginAdmin(
  username: string,
  password: string,
): Promise<AdminLoginResponse> {
  const response = await apiClient.post<AdminLoginResponse>('/v1/auth/login', {
    username,
    password,
  })
  return response.data
}

export async function getCurrentAdmin(): Promise<AdminUser> {
  const response = await apiClient.get<AdminUser>('/v1/auth/me')
  return response.data
}
