export type User = { userid: string; name: string; email: string; roles: string[]; companies: string[] }

export type SessionClient = {
  me: () => Promise<User | null>
  login: (email: string, password: string) => Promise<boolean>
  logout: () => Promise<void>
}

const mockUsers: User[] = [
  { userid: 'u-manager', name: 'Mock Manager', email: 'manager@mock-sami.com', roles: ['management'], companies: ['sabinsa', 'neutraceuticals'] },
  { userid: 'u-admin', name: 'Mock Admin', email: 'admin@mock-sami.com', roles: ['admin'], companies: ['sabinsa', 'neutraceuticals', 'organica'] },
  { userid: 'u-sales', name: 'Mock Sales', email: 'sales@mock-sami.com', roles: ['sales'], companies: ['organica'] },
]

const MOCK_PASSWORD = 'mock'

export class MockSessionClient implements SessionClient {
  private current: User | null

  constructor(signedInAs: string | null = null) {
    this.current = mockUsers.find((user) => user.email === signedInAs) ?? null
  }

  async me() {
    return this.current
  }

  async login(email: string, password: string) {
    const user = mockUsers.find((candidate) => candidate.email === email)
    if (!user || password !== MOCK_PASSWORD) return false
    this.current = user
    return true
  }

  async logout() {
    this.current = null
  }
}
