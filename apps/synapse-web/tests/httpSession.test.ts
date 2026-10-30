import { HttpSessionClient } from '../src/session/httpSessionClient'

const respond = (status: number, body: unknown = {}) => vi.fn(async () => new Response(JSON.stringify(body), { status }))

const stub = (fetchMock: ReturnType<typeof respond>) => {
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => vi.unstubAllGlobals())

describe('signing in', () => {
  it('posts the form to auth-api with credentials and reports success', async () => {
    const fetchMock = stub(respond(200, { message: 'Logged in' }))
    expect(await new HttpSessionClient().login('manager@sami.com', 'secret')).toBe(true)
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('http://localhost:8001/v1/auth/login/password')
    expect(init.credentials).toBe('include')
    expect(String(init.body)).toBe('username=manager%40sami.com&password=secret')
  })

  it('returns false for a wrong password', async () => {
    stub(respond(401))
    expect(await new HttpSessionClient().login('a@b.com', 'wrong')).toBe(false)
  })

  it('throws on a server error', async () => {
    stub(respond(500))
    await expect(new HttpSessionClient().login('a@b.com', 'x')).rejects.toThrow('auth login failed: 500')
  })
})

describe('the current user', () => {
  it('maps /me to a user and sends credentials', async () => {
    const fetchMock = stub(respond(200, { userid: 'u1', sap_username: 'SMITH', roles: ['management'] }))
    expect(await new HttpSessionClient().me()).toEqual({ userid: 'u1', name: 'SMITH', email: '', roles: ['management'] })
    expect((fetchMock.mock.calls[0] as unknown as [string, RequestInit])[1].credentials).toBe('include')
  })

  it('is signed out on 401', async () => {
    stub(respond(401))
    expect(await new HttpSessionClient().me()).toBeNull()
  })

  it('throws on a server error', async () => {
    stub(respond(503))
    await expect(new HttpSessionClient().me()).rejects.toThrow('auth me failed: 503')
  })
})

describe('signing out', () => {
  it('posts to the logout endpoint with credentials', async () => {
    const fetchMock = stub(respond(200))
    await new HttpSessionClient().logout()
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('http://localhost:8001/v1/auth/logout')
    expect(init).toMatchObject({ method: 'POST', credentials: 'include' })
  })
})
