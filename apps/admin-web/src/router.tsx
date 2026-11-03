import { createRootRouteWithContext, createRoute, createRouter, redirect, Outlet, useRouteContext } from '@tanstack/react-router'
import type { RouterHistory } from '@tanstack/react-router'
import type { AdminClient } from './api/adminClient'
import type { Session } from './session/useSession'
import { LoginPage } from './pages/LoginPage'
import { NotAllowedPage } from './pages/NotAllowedPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { UsersPage } from './pages/UsersPage'
import { AuditPage } from './pages/AuditPage'
import type { AuditSearch } from './pages/AuditPage'
import { Shell } from './Shell'

export type RouterContext = {
  session: Session
  login: (username: string, password: string) => Promise<boolean>
  logout: () => Promise<void>
  admin: AdminClient
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

const rootRoute = createRootRouteWithContext<RouterContext>()({ component: RootLayout, notFoundComponent: NotFoundPage })

const requireAdmin = ({ context }: { context: RouterContext }) => {
  if (context.session.status === 'signedOut') throw redirect({ to: '/login' })
  if (context.session.status === 'signedIn' && !context.session.user.roles.includes('admin')) throw redirect({ to: '/not-allowed' })
}

export const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  beforeLoad: ({ context }) => {
    if (context.session.status === 'signedIn') throw redirect({ to: '/users' })
  },
  component: LoginPage,
})

const homeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  beforeLoad: () => {
    throw redirect({ to: '/users' })
  },
})

const notAllowedRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/not-allowed',
  beforeLoad: ({ context }) => {
    if (context.session.status === 'signedOut') throw redirect({ to: '/login' })
  },
  component: NotAllowedPage,
})

const usersRoute = createRoute({ getParentRoute: () => rootRoute, path: '/users', beforeLoad: requireAdmin, component: UsersPage })

const text = (value: unknown) => (typeof value === 'string' && value !== '' ? value : undefined)

const auditRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/audit',
  validateSearch: (search: Record<string, unknown>): AuditSearch => ({
    actor: text(search.actor),
    action: text(search.action),
    outcome: text(search.outcome),
    from: text(search.from),
    to: text(search.to),
  }),
  beforeLoad: requireAdmin,
  component: AuditPage,
})

const routeTree = rootRoute.addChildren([loginRoute, homeRoute, notAllowedRoute, usersRoute, auditRoute])

export const createAppRouter = (context: RouterContext, history?: RouterHistory) => createRouter({ routeTree, context, history })

declare module '@tanstack/react-router' {
  interface Register {
    router: ReturnType<typeof createAppRouter>
  }
}
