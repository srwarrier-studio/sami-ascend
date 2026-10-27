import { AUTH_URL } from '../config'

export type User = { userid: string; sap_username: string; roles: string[] }

export type AuthClient = {
  me: () => Promise<User | null>
  login: (username: string, password: string) => Promise<boolean>
  logout: () => Promise<void>
}

const call = (path: string, init: RequestInit = {}) =>
  fetch(`${AUTH_URL}/v1/auth${path}`, { credentials: 'include', ...init })

export const authClient: AuthClient = {
  async me() {
    const response = await call('/me')
    if (response.status === 401) return null
    if (!response.ok) throw new Error(`auth me failed: ${response.status}`)
    return response.json()
  },
  async login(username, password) {
    const response = await call('/login/password', {
      method: 'POST',
      body: new URLSearchParams({ username, password }),
    })
    if (response.status === 401) return false
    if (!response.ok) throw new Error(`auth login failed: ${response.status}`)
    return true
  },
  async logout() {
    await call('/logout', { method: 'POST' })
  },
}

export const entraLoginUrl = `${AUTH_URL}/v1/auth/login/entra`
