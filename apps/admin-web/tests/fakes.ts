import type { AdminClient, AdminUser, AuditEntry } from '../src/api/adminClient'
import { AdminError } from '../src/api/adminClient'

export const user = (patch: Partial<AdminUser> = {}): AdminUser => ({
  userid: 'u1',
  email: 'bob@sami.com',
  fullname: 'Bob',
  sap_username: 'BOB',
  entra_username: null,
  roles: ['production'],
  companies: ['sabinsa'],
  disabled: false,
  has_password: true,
  created_at: '2026-11-03T10:00:00',
  ...patch,
})

export const entry = (id: number, patch: Partial<AuditEntry> = {}): AuditEntry => ({
  id,
  at: '2026-11-03T10:00:00+00:00',
  actor: 'bob@sami.com',
  action: 'login.password',
  target: 'bob@sami.com',
  outcome: 'success',
  detail: '',
  ...patch,
})

export const fakeAdmin = (users: AdminUser[] = [user()], audit: AuditEntry[] = []): AdminClient & { calls: string[] } => {
  const calls: string[] = []
  return {
    calls,
    users: async (query) => users.filter((candidate) => `${candidate.fullname} ${candidate.email}`.toLowerCase().includes(query.toLowerCase())),
    createUser: async (input) => {
      calls.push(`create ${input.email}`)
      if (users.some((candidate) => candidate.email === input.email)) throw new AdminError('USER_ALREADY_EXISTS', 'exists')
      const created = user({ userid: 'new', email: input.email, fullname: input.fullname, roles: input.roles })
      users.push(created)
      return created
    },
    updateUser: async (userid, changes) => {
      calls.push(`update ${userid} ${JSON.stringify(changes)}`)
      if (changes.disabled === false && userid === 'last') throw new AdminError('LAST_ADMIN', 'x')
      const found = users.find((candidate) => candidate.userid === userid)!
      Object.assign(found, changes)
      return found
    },
    roles: async () => ['admin', 'production', 'accounts'],
    companies: async () => ['sabinsa', 'organica'],
    audit: async (filters, before, limit = 50) => {
      calls.push(`audit ${JSON.stringify(filters)} ${before} ${limit}`)
      const rows = audit
        .filter((row) => (!filters.outcome || row.outcome === filters.outcome) && (!filters.actor || row.actor === filters.actor) && (!filters.action || row.action === filters.action))
        .filter((row) => before === null || row.id < before)
        .sort((a, b) => b.id - a.id)
      const items = rows.slice(0, limit)
      return { items, next: rows.length > limit ? items[items.length - 1].id : null }
    },
  }
}
