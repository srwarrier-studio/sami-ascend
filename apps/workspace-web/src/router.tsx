import {
  createRootRouteWithContext,
  createRoute,
  createRouter,
  redirect,
  Outlet,
} from '@tanstack/react-router'
import type { RouterHistory } from '@tanstack/react-router'
import type { Session } from './session/useSession'
import { LoginPage } from './pages/LoginPage'
import { HomePage } from './pages/HomePage'
import { NotAllowedPage } from './pages/NotAllowedPage'
import { NotFoundPage } from './pages/NotFoundPage'

export type RouterContext = {
  session: Session
  login: (username: string, password: string) => Promise<boolean>
  logout: () => Promise<void>
}

const rootRoute = createRootRouteWithContext<RouterContext>()({
  component: Outlet,
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

const routeTree = rootRoute.addChildren([loginRoute, homeRoute, notAllowedRoute])

export const createAppRouter = (context: RouterContext, history?: RouterHistory) =>
  createRouter({ routeTree, context, history })

declare module '@tanstack/react-router' {
  interface Register {
    router: ReturnType<typeof createAppRouter>
  }
}
