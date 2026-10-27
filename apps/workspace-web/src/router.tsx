import {
  createRootRouteWithContext,
  createRoute,
  createRouter,
  redirect,
  Outlet,
  useRouteContext,
} from '@tanstack/react-router'
import type { RouterHistory } from '@tanstack/react-router'
import type { SalesOrderClient } from './api/salesOrders'
import type { Session } from './session/useSession'
import { LoginPage } from './pages/LoginPage'
import { HomePage } from './pages/HomePage'
import { NotAllowedPage } from './pages/NotAllowedPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { ComingSoonPage } from './pages/ComingSoonPage'
import { Shell } from './Shell'
import { allowedEntries } from './menu'

export type RouterContext = {
  session: Session
  login: (username: string, password: string) => Promise<boolean>
  logout: () => Promise<void>
  salesOrders: SalesOrderClient
}

function RootLayout() {
  const { session, logout } = useRouteContext({ from: '__root__' })
  if (session.status !== 'signedIn') return <Outlet />
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

export const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  validateSearch: (search: Record<string, unknown>): { error?: string } =>
    typeof search.error === 'string' ? { error: search.error } : {},
  beforeLoad: ({ context }) => {
    if (context.session.status === 'signedIn') throw redirect({ to: '/' })
  },
  component: LoginPage,
})

const homeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  beforeLoad: requireSignedIn,
  component: HomePage,
})

const notAllowedRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/not-allowed',
  beforeLoad: requireSignedIn,
  component: NotAllowedPage,
})

const salesOrdersRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/sales-orders',
  beforeLoad: ({ context }) => {
    requireSignedIn({ context })
    if (context.session.status !== 'signedIn') return
    const allowed = allowedEntries(context.session.user.roles).some((e) => e.path === '/sales-orders')
    if (!allowed) throw redirect({ to: '/not-allowed' })
  },
  component: ComingSoonPage,
})

const routeTree = rootRoute.addChildren([loginRoute, homeRoute, notAllowedRoute, salesOrdersRoute])

export const createAppRouter = (context: RouterContext, history?: RouterHistory) =>
  createRouter({ routeTree, context, history })

declare module '@tanstack/react-router' {
  interface Register {
    router: ReturnType<typeof createAppRouter>
  }
}
