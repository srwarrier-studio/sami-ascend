import { useCallback, useEffect, useState } from 'react'
import type { AuthClient, User } from '../api/auth'

export type Session =
  | { status: 'loading' }
  | { status: 'signedOut' }
  | { status: 'signedIn'; user: User }

export function useSession(client: AuthClient) {
  const [session, setSession] = useState<Session>({ status: 'loading' })

  const refresh = useCallback(async () => {
    const user = await client.me()
    setSession(user ? { status: 'signedIn', user } : { status: 'signedOut' })
  }, [client])

  useEffect(() => {
    refresh()
  }, [refresh])

  const login = useCallback(
    async (username: string, password: string) => {
      const ok = await client.login(username, password)
      if (ok) await refresh()
      return ok
    },
    [client, refresh],
  )

  const logout = useCallback(async () => {
    await client.logout()
    setSession({ status: 'signedOut' })
  }, [client])

  return { session, login, logout }
}
