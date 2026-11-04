import { useEffect, useRef, useState } from 'react'
import { RouterProvider } from '@tanstack/react-router'
import type { RouterHistory } from '@tanstack/react-router'
import { Alert, Button, Container, Loader, Stack } from '@sami/ui'
import type { AuthClient } from './api/auth'
import { purchaseRequisitionClient } from './api/purchaseRequisitions'
import type { PurchaseRequisitionClient } from './api/purchaseRequisitions'
import { salesOrderClient } from './api/salesOrders'
import type { SalesOrderClient } from './api/salesOrders'
import { createAppRouter } from './router'
import type { RouterContext } from './router'
import { useSession } from './session/useSession'

type AppProps = {
  client: AuthClient
  salesOrders?: SalesOrderClient
  purchaseRequisitions?: PurchaseRequisitionClient
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

export default function App({
  client,
  salesOrders = salesOrderClient,
  purchaseRequisitions = purchaseRequisitionClient,
  history,
}: AppProps) {
  const { session, login, logout, retry } = useSession(client)
  if (session.status === 'loading') return <Loader />
  if (session.status === 'unavailable')
    return (
      <Container size="xs" py="xl">
        <Stack>
          <Alert color="red" title="Cannot reach the sign-in service">
            Check that auth-api is running, then try again.
          </Alert>
          <Button onClick={retry}>Try again</Button>
        </Stack>
      </Container>
    )
  return <Routed context={{ session, login, logout, salesOrders, purchaseRequisitions }} history={history} />
}
