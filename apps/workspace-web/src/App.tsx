import { useEffect, useState } from 'react'
import { RouterProvider } from '@tanstack/react-router'
import type { RouterHistory } from '@tanstack/react-router'
import { Loader } from '@sami/ui'
import type { AuthClient } from './api/auth'
import { createAppRouter } from './router'
import { useSession } from './session/useSession'

type AppProps = { client: AuthClient; history?: RouterHistory }

export default function App({ client, history }: AppProps) {
  const { session, login, logout } = useSession(client)
  const context = { session, login, logout }
  const [router] = useState(() => createAppRouter(context, history))

  useEffect(() => {
    router.update({ context })
    router.invalidate()
  }, [session])

  if (session.status === 'loading') return <Loader />
  return <RouterProvider router={router} context={context} />
}
