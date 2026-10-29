import { useEffect, useRef, useState } from 'react'
import { RouterProvider } from '@tanstack/react-router'
import type { RouterHistory } from '@tanstack/react-router'
import { SplashScreen } from '@sami/ui'
import { MockSalesData } from './data/mockSalesData'
import type { SalesData } from './data/salesData'
import { createAppRouter } from './router'
import type { RouterContext } from './router'
import type { SessionClient } from './session/sessionClient'
import { useSession } from './session/useSession'

type AppProps = { client: SessionClient; salesData?: SalesData; history?: RouterHistory }

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

const defaultSalesData = new MockSalesData()

export default function App({ client, salesData = defaultSalesData, history }: AppProps) {
  const { session, login, logout } = useSession(client)
  if (session.status === 'loading') return <SplashScreen name="Synapse" tagline="Your sales, on one board" />
  return <Routed context={{ session, login, logout, salesData }} history={history} />
}
