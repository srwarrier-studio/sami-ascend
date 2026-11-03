import { AUTH_URL } from '../config'

export type AdminUser = {
  userid: string
  email: string
  fullname: string
  sap_username: string
  entra_username: string | null
  roles: string[]
  companies: string[]
  disabled: boolean
  has_password: boolean
  created_at: string
}

export type UserInput = {
  email: string
  fullname: string
  sap_username: string
  entra_username: string | null
  roles: string[]
  companies: string[]
  password: string
}

export type UserChanges = Partial<Omit<UserInput, 'email' | 'password'>> & { disabled?: boolean }

export type AuditEntry = { id: number; at: string; actor: string; action: string; target: string; outcome: string; detail: string }
export type AuditFilters = { actor?: string; action?: string; outcome?: string; from?: string; to?: string }
export type AuditPage = { items: AuditEntry[]; next: number | null }

export class AdminError extends Error {
  code: string

  constructor(code: string, message: string) {
    super(message)
    this.code = code
  }
}

export type AdminClient = {
  users: (query: string) => Promise<AdminUser[]>
  createUser: (input: UserInput) => Promise<AdminUser>
  updateUser: (userid: string, changes: UserChanges) => Promise<AdminUser>
  roles: () => Promise<string[]>
  companies: () => Promise<string[]>
  audit: (filters: AuditFilters, before: number | null, limit?: number) => Promise<AuditPage>
}

const call = async (method: string, path: string, body?: object) => {
  const response = await fetch(`${AUTH_URL}/v1/auth/admin${path}`, {
    method,
    credentials: 'include',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await response.json().catch(() => ({}))
  if (response.ok) return data
  const detail = data.detail
  if (detail && typeof detail === 'object' && 'code' in detail) throw new AdminError(detail.code, detail.message)
  throw new AdminError(`HTTP_${response.status}`, typeof detail === 'string' ? detail : 'The request failed')
}

const queryOf = (values: Record<string, string | number | null | undefined>) => {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(values)) if (value !== undefined && value !== null && value !== '') params.set(key, String(value))
  return params.size > 0 ? `?${params}` : ''
}

export const adminClient: AdminClient = {
  users: (query) => call('GET', `/users${queryOf({ q: query })}`),
  createUser: (input) => call('POST', '/users', { ...input, entra_username: input.entra_username || null }),
  updateUser: (userid, changes) => call('PATCH', `/users/${userid}`, changes),
  roles: () => call('GET', '/roles'),
  companies: () => call('GET', '/companies'),
  audit: (filters, before, limit = 50) => call('GET', `/audit-log${queryOf({ ...filters, before, limit })}`),
}
