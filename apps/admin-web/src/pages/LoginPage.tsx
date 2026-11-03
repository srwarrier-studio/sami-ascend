import { useState } from 'react'
import type { SyntheticEvent } from 'react'
import { useRouteContext } from '@tanstack/react-router'
import { Alert, Button, Container, PasswordInput, Stack, TextInput, Title } from '@sami/ui'

export function LoginPage() {
  const { login } = useRouteContext({ from: '/login' })
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
          {rejected && <Alert color="red">Incorrect username or password</Alert>}
          <TextInput label="Username" value={username} onChange={(e) => setUsername(e.currentTarget.value)} />
          <PasswordInput label="Password" value={password} onChange={(e) => setPassword(e.currentTarget.value)} />
          <Button type="submit">Sign in</Button>
        </Stack>
      </form>
    </Container>
  )
}
