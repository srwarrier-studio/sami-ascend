import { AUTH_URL } from '../config'
import { knownCompanyIds } from './companies'
import type { SessionClient, User } from './sessionClient'

type Me = { userid: string; sap_username: string; roles: string[]; companies: string[] }

const call = (path: string, init: RequestInit = {}) => fetch(`${AUTH_URL}/v1/auth${path}`, { credentials: 'include', ...init })

export class HttpSessionClient implements SessionClient {
  async me(): Promise<User | null> {
    const response = await call('/me')
    if (response.status === 401) return null
    if (!response.ok) throw new Error(`auth me failed: ${response.status}`)
    const me: Me = await response.json()
    return { userid: me.userid, name: me.sap_username, email: '', roles: me.roles, companies: knownCompanyIds(me.companies) }
  }

  async login(email: string, password: string) {
    const response = await call('/login/password', { method: 'POST', body: new URLSearchParams({ username: email, password }) })
    if (response.status === 401) return false
    if (!response.ok) throw new Error(`auth login failed: ${response.status}`)
    return true
  }

  async logout() {
    await call('/logout', { method: 'POST' })
  }
}
