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
  const token = config.url?.includes('/v1/users') ? getUserToken() : getAdminToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (error.config?.url?.includes('/v1/users')) clearUserSession()
      else clearAdminSession()
    }
    return Promise.reject(error)
  },
)
