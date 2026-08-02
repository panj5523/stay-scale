const TOKEN_KEY = 'stay_scale_admin_token'
const USER_KEY = 'stay_scale_admin_user'

export function getAdminToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY)
}

export function saveAdminSession(token: string, user: unknown): void {
  sessionStorage.setItem(TOKEN_KEY, token)
  sessionStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearAdminSession(): void {
  sessionStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(USER_KEY)
}

export function hasAdminSession(): boolean {
  return Boolean(getAdminToken())
}
