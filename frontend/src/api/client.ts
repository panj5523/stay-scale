import axios from 'axios'
import { clearAdminSession, getAdminToken } from '../auth/session'
import { clearUserSession, getUserToken } from '../auth/userSession'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  timeout: 8_000,
  headers: {
    Accept: 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const isManagementRequest = config.url?.includes('/v1/management') || config.url?.includes('/v1/auth')
  const token = isManagementRequest ? getAdminToken() : getUserToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const isManagementRequest = error.config?.url?.includes('/v1/management') || error.config?.url?.includes('/v1/auth')
      if (isManagementRequest) clearAdminSession()
      else clearUserSession()
    }
    return Promise.reject(error)
  },
)
