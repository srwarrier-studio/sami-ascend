import { useState } from 'react'
import { useRouteContext } from '@tanstack/react-router'
import { Container, SignInCard } from '@sami/ui'

export function LoginPage() {
  const { login } = useRouteContext({ from: '/login' })
  const [rejected, setRejected] = useState(false)

  return (
    <Container py="xl">
      <SignInCard
        title="Sign in to Synapse"
        error={rejected ? 'Incorrect email or password' : undefined}
        onSubmit={async (email, password) => setRejected(!(await login(email, password)))}
      />
    </Container>
  )
}
