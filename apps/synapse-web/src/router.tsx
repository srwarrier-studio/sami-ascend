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
import type { SalesData } from './data/salesData'
import type { Session } from './session/useSession'
import type { ChatPlanner } from './ai/chatPlanner'
import { canUseSynapse } from './access'
import { AiPage } from './pages/AiPage'
import { BoardsPage } from './pages/BoardsPage'
import { LoginPage } from './pages/LoginPage'
import { NotAllowedPage } from './pages/NotAllowedPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { WidgetsPage } from './pages/WidgetsPage'
import { Shell } from './Shell'

export type UiSettings = { palette: PresetName; motion: MotionMode }

export type RouterContext = {
  session: Session
  login: (email: string, password: string) => Promise<boolean>
  logout: () => Promise<void>
  salesData: SalesData
  boardStore: BoardStore
  chatPlanner: ChatPlanner
  ui: UiSettings
  setUi: (ui: UiSettings) => void
}

function RootLayout() {
  const { session, logout } = useRouteContext({ from: '__root__' })
  const path = useRouterState({ select: (state) => state.location.pathname })
  if (session.status !== 'signedIn' || path === '/ai') return <Outlet />
  return (
    <Shell user={session.user} onLogout={logout}>
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
  beforeLoad: requireSynapseAccess,
  component: BoardsPage,
})

const widgetsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/widgets',
  beforeLoad: requireSynapseAccess,
  component: WidgetsPage,
})

const aiRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/ai',
  beforeLoad: requireSynapseAccess,
  component: AiPage,
})

const notAllowedRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/not-allowed',
  beforeLoad: requireSignedIn,
  component: NotAllowedPage,
})

const routeTree = rootRoute.addChildren([loginRoute, boardsRoute, aiRoute, widgetsRoute, notAllowedRoute])

export const createAppRouter = (context: RouterContext, history?: RouterHistory) =>
  createRouter({ routeTree, context, history })

declare module '@tanstack/react-router' {
  interface Register {
    router: ReturnType<typeof createAppRouter>
  }
}
