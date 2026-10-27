import { useEffect, useRef, useState } from 'react'
import { RouterProvider } from '@tanstack/react-router'
import type { RouterHistory } from '@tanstack/react-router'
import { Loader } from '@sami/ui'
import type { AuthClient } from './api/auth'
import { salesOrderClient } from './api/salesOrders'
import type { SalesOrderClient } from './api/salesOrders'
import { createAppRouter } from './router'
import type { RouterContext } from './router'
import { useSession } from './session/useSession'

type AppProps = { client: AuthClient; salesOrders?: SalesOrderClient; history?: RouterHistory }

function Routed({ context, history }: { context: RouterContext; history?: RouterHistory }) {
  const [router] = useState(() => createAppRouter(context, history))

  const loadedSession = useRef(context.session)

  useEffect(() => {
    if (loadedSession.current === context.session) return
    loadedSession.current = context.session
    router.invalidate()
  }, [router, context.session])

  return <RouterProvider router={router} context={context} />
}

export default function App({ client, salesOrders = salesOrderClient, history }: AppProps) {
  const { session, login, logout } = useSession(client)
  if (session.status === 'loading') return <Loader />
  return <Routed context={{ session, login, logout, salesOrders }} history={history} />
}
