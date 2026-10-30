import { useEffect, useRef, useState } from 'react'
import { RouterProvider } from '@tanstack/react-router'
import type { RouterHistory } from '@tanstack/react-router'
import { Alert, Button, Container, SplashScreen, Stack } from '@sami/ui'
import { MockBoardStore } from './boards/boardStore'
import type { BoardStore } from './boards/boardStore'
import { MockChatPlanner } from './ai/chatPlanner'
import type { ChatPlanner } from './ai/chatPlanner'
import { MockBoardExporter } from './export/boardExporter'
import type { BoardExporter } from './export/boardExporter'
import { MockCatalogClient } from './catalog/mockCatalogClient'
import type { CatalogClient } from './catalog/catalogClient'
import { useCatalog } from './catalog/useCatalog'
import { createAppRouter } from './router'
import type { RouterContext, UiSettings } from './router'
import type { SessionClient } from './session/sessionClient'
import { useCompany } from './session/useCompany'
import { useSession } from './session/useSession'

type AppProps = {
  client: SessionClient
  boardStore?: BoardStore
  chatPlanner?: ChatPlanner
  catalogClient?: CatalogClient
  boardExporter?: BoardExporter
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

const defaultBoardStore = new MockBoardStore()
const defaultCatalogClient = new MockCatalogClient()
const defaultBoardExporter = new MockBoardExporter()
const defaultChatPlanner = new MockChatPlanner()
const defaultUi: UiSettings = { palette: 'teal', motion: 'full' }

export default function App({ client, boardStore = defaultBoardStore, chatPlanner = defaultChatPlanner, catalogClient = defaultCatalogClient, boardExporter = defaultBoardExporter, ui = defaultUi, onUiChange = () => undefined, history }: AppProps) {
  const { session, login, logout, retry } = useSession(client)
  const { company, setCompany } = useCompany(session.status === 'signedIn' ? session.user : null)
  const { state: catalog, retry: retryCatalog } = useCatalog(catalogClient, session.status === 'signedIn')
  if (session.status === 'loading' || (session.status === 'signedIn' && catalog.status !== 'ready' && catalog.status !== 'failed')) return <SplashScreen name="Synapse" tagline="Your sales, on one board" />
  if (session.status === 'unreachable' || (session.status === 'signedIn' && catalog.status === 'failed'))
    return (
      <Container py="xl">
        <Stack align="flex-start">
          <Alert color="red" title="Cannot reach the server">
            Check that the login and Synapse services are running and try again.
          </Alert>
          <Button onClick={session.status === 'unreachable' ? retry : retryCatalog}>Try again</Button>
        </Stack>
      </Container>
    )
  return <Routed context={{ session, login, logout, catalogClient, catalog: catalog.status === 'ready' ? catalog.entries : [], boardStore, chatPlanner, boardExporter, company, setCompany, ui, setUi: onUiChange }} history={history} />
}
