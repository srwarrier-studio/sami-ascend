import {
  createRootRouteWithContext,
  createRoute,
  createRouter,
  redirect,
  Outlet,
  useRouteContext,
  useRouterState,
} from '@tanstack/react-router'
import type { RouterHistory } from '@tanstack/react-router'
import type { BoardStore } from './boards/boardStore'
import type { PresetName, MotionMode } from '@sami/ui'
import type { CatalogClient, CatalogEntry } from './catalog/catalogClient'
import type { Session } from './session/useSession'
import type { AgentsClient } from './ai/agentsClient'
import type { IntentClient } from './ai/intentClient'
import type { ChatPlanner } from './ai/chatPlanner'
import type { BoardExporter } from './export/boardExporter'
import { canUseSynapse } from './access'
import { AiPage } from './pages/AiPage'
import { CompanyPage } from './pages/CompanyPage'
import { NoCompanyPage } from './pages/NoCompanyPage'
import { BoardsPage } from './pages/BoardsPage'
import { LoginPage } from './pages/LoginPage'
import { NotAllowedPage } from './pages/NotAllowedPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { ReportsPage } from './pages/ReportsPage'
import { Shell } from './Shell'

export type UiSettings = { palette: PresetName; motion: MotionMode }

export type RouterContext = {
  session: Session
  login: (email: string, password: string) => Promise<boolean>
  logout: () => Promise<void>
  catalogClient: CatalogClient
  catalog: CatalogEntry[]
  boardStore: BoardStore
  chatPlanner: ChatPlanner
  agentsClient: AgentsClient
  intentClient: IntentClient
  boardExporter: BoardExporter
  company: string | null
  setCompany: (id: string) => void
  ui: UiSettings
  setUi: (ui: UiSettings) => void
}

function RootLayout() {
  const { session, company, logout } = useRouteContext({ from: '__root__' })
  const path = useRouterState({ select: (state) => state.location.pathname })
  if (session.status !== 'signedIn' || path === '/ai' || path === '/company' || path === '/no-company') return <Outlet />
  return (
    <Shell user={session.user} company={company} onLogout={logout}>
      <Outlet />
    </Shell>
  )
}

const rootRoute = createRootRouteWithContext<RouterContext>()({
  component: RootLayout,
  notFoundComponent: NotFoundPage,
})

const requireSignedIn = ({ context }: { context: RouterContext }) => {
  if (context.session.status === 'signedOut') throw redirect({ to: '/login' })
}

const requireSynapseAccess = ({ context }: { context: RouterContext }) => {
  requireSignedIn({ context })
  if (context.session.status === 'signedIn' && !canUseSynapse(context.session.user.roles)) {
    throw redirect({ to: '/not-allowed' })
  }
}

const requireCompany = ({ context }: { context: RouterContext }) => {
  requireSynapseAccess({ context })
  if (context.session.status !== 'signedIn' || context.company) return
  throw redirect({ to: context.session.user.companies.length === 0 ? '/no-company' : '/company' })
}

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  beforeLoad: ({ context }) => {
    if (context.session.status === 'signedIn') throw redirect({ to: '/' })
  },
  component: LoginPage,
})

const boardsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  validateSearch: (search: Record<string, unknown>) => ({ board: typeof search.board === 'string' ? search.board : undefined }),
  beforeLoad: requireCompany,
  component: BoardsPage,
})

const reportsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/reports',
  beforeLoad: requireCompany,
  component: ReportsPage,
})

const aiRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/ai',
  beforeLoad: requireCompany,
  component: AiPage,
})

const companyRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/company',
  beforeLoad: ({ context }) => {
    requireSynapseAccess({ context })
    if (context.session.status !== 'signedIn') return
    const count = context.session.user.companies.length
    if (count === 0) throw redirect({ to: '/no-company' })
    if (count === 1) throw redirect({ to: '/', search: { board: undefined } })
  },
  component: CompanyPage,
})

const noCompanyRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/no-company',
  beforeLoad: requireSynapseAccess,
  component: NoCompanyPage,
})

const notAllowedRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/not-allowed',
  beforeLoad: requireSignedIn,
  component: NotAllowedPage,
})

const routeTree = rootRoute.addChildren([loginRoute, boardsRoute, aiRoute, reportsRoute, companyRoute, noCompanyRoute, notAllowedRoute])

export const createAppRouter = (context: RouterContext, history?: RouterHistory) =>
  createRouter({ routeTree, context, history })

declare module '@tanstack/react-router' {
  interface Register {
    router: ReturnType<typeof createAppRouter>
  }
}
