export interface AdminUser {
  public_id: string
  username: string
  display_name: string
  role: string
}

export interface AdminLoginResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: AdminUser
}
