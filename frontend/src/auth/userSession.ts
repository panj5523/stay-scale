const TOKEN_KEY = 'stay_scale_user_token'
const USER_KEY = 'stay_scale_user'

export function getUserToken(): string | null { return localStorage.getItem(TOKEN_KEY) }
export function hasUserSession(): boolean { return Boolean(getUserToken()) }
export function saveUserSession(token: string, user: unknown): void {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}
export function clearUserSession(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}
