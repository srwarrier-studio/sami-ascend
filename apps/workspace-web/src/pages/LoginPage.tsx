import { useState } from 'react'
import type { SyntheticEvent } from 'react'
import { useRouteContext, useSearch } from '@tanstack/react-router'
import { Alert, Button, Container, PasswordInput, Stack, TextInput, Title } from '@sami/ui'
import { entraLoginUrl } from '../api/auth'

export function LoginPage() {
  const { login } = useRouteContext({ from: '/login' })
  const { error } = useSearch({ from: '/login' })
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [rejected, setRejected] = useState(false)

  const submit = async (event: SyntheticEvent) => {
    event.preventDefault()
    setRejected(!(await login(username, password)))
  }

  return (
    <Container size="xs" py="xl">
      <form onSubmit={submit}>
        <Stack>
          <Title order={2}>Sign in</Title>
          {error === 'entra' && (
            <Alert color="red">Microsoft sign-in failed. Ask an admin to check your account.</Alert>
          )}
          {rejected && <Alert color="red">Incorrect username or password</Alert>}
          <TextInput label="Username" value={username} onChange={(e) => setUsername(e.currentTarget.value)} />
          <PasswordInput label="Password" value={password} onChange={(e) => setPassword(e.currentTarget.value)} />
          <Button type="submit">Sign in</Button>
          <Button component="a" href={entraLoginUrl} variant="default">
            Sign in with Microsoft
          </Button>
        </Stack>
      </form>
    </Container>
  )
}
