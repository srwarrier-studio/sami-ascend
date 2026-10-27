import { renderHook, waitFor, act } from '@testing-library/react'
import type { AuthClient, User } from '../src/api/auth'
import { useSession } from '../src/session/useSession'

const sales: User = { userid: 'u1', sap_username: 'ANNA', roles: ['sales'] }

const fakeClient = (user: User | null, loginOk = true): AuthClient => ({
  me: vi.fn().mockResolvedValue(user),
  login: vi.fn().mockResolvedValue(loginOk),
  logout: vi.fn().mockResolvedValue(undefined),
})

describe('session on load', () => {
  it('is loading until me answers', async () => {
    const client = fakeClient(sales)
    const { result } = renderHook(() => useSession(client))
    expect(result.current.session.status).toBe('loading')
    await waitFor(() => expect(result.current.session.status).toBe('signedIn'))
  })

  it('is signed out when me returns nothing', async () => {
    const client = fakeClient(null)
    const { result } = renderHook(() => useSession(client))
    await waitFor(() => expect(result.current.session.status).toBe('signedOut'))
  })
})

describe('login', () => {
  it('loads me after good credentials', async () => {
    const client = fakeClient(null)
    const { result } = renderHook(() => useSession(client))
    await waitFor(() => expect(result.current.session.status).toBe('signedOut'))
    vi.mocked(client.me).mockResolvedValue(sales)
    let ok = false
    await act(async () => {
      ok = await result.current.login('anna', 'pw')
    })
    expect(ok).toBe(true)
    expect(result.current.session).toEqual({ status: 'signedIn', user: sales })
  })

  it('stays signed out and returns false on bad credentials', async () => {
    const client = fakeClient(null, false)
    const { result } = renderHook(() => useSession(client))
    await waitFor(() => expect(result.current.session.status).toBe('signedOut'))
    let ok = true
    await act(async () => {
      ok = await result.current.login('anna', 'bad')
    })
    expect(ok).toBe(false)
    expect(result.current.session.status).toBe('signedOut')
  })
})

describe('logout', () => {
  it('signs out', async () => {
    const client = fakeClient(sales)
    const { result } = renderHook(() => useSession(client))
    await waitFor(() => expect(result.current.session.status).toBe('signedIn'))
    await act(async () => {
      await result.current.logout()
    })
    expect(client.logout).toHaveBeenCalled()
    expect(result.current.session.status).toBe('signedOut')
  })
})
