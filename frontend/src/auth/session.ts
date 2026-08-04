const TOKEN_KEY = 'stay_scale_admin_token'
const USER_KEY = 'stay_scale_admin_user'
export const ADMIN_SESSION_EVENT = 'stay-scale-admin-session-change'

export function getAdminToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY)
}

export function saveAdminSession(token: string, user: unknown): void {
  sessionStorage.setItem(TOKEN_KEY, token)
  sessionStorage.setItem(USER_KEY, JSON.stringify(user))
  window.dispatchEvent(new Event(ADMIN_SESSION_EVENT))
}

export function clearAdminSession(): void {
  sessionStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(USER_KEY)
  window.dispatchEvent(new Event(ADMIN_SESSION_EVENT))
}

export function hasAdminSession(): boolean {
  return Boolean(getAdminToken())
}
