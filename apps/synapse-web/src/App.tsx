import { useEffect, useRef, useState } from 'react'
import { RouterProvider } from '@tanstack/react-router'
import type { RouterHistory } from '@tanstack/react-router'
import { SplashScreen } from '@sami/ui'
import { MockSalesData } from './data/mockSalesData'
import type { SalesData } from './data/salesData'
import { MockBoardStore } from './boards/boardStore'
import type { BoardStore } from './boards/boardStore'
import { createAppRouter } from './router'
import type { RouterContext, UiSettings } from './router'
import type { SessionClient } from './session/sessionClient'
import { useSession } from './session/useSession'

type AppProps = {
  client: SessionClient
  salesData?: SalesData
  boardStore?: BoardStore
  ui?: UiSettings
  onUiChange?: (ui: UiSettings) => void
  history?: RouterHistory
}

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
const defaultBoardStore = new MockBoardStore()
const defaultUi: UiSettings = { palette: 'teal', motion: 'full' }

export default function App({ client, salesData = defaultSalesData, boardStore = defaultBoardStore, ui = defaultUi, onUiChange = () => undefined, history }: AppProps) {
  const { session, login, logout } = useSession(client)
  if (session.status === 'loading') return <SplashScreen name="Synapse" tagline="Your sales, on one board" />
  return <Routed context={{ session, login, logout, salesData, boardStore, ui, setUi: onUiChange }} history={history} />
}
