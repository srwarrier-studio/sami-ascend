import { useRouteContext } from '@tanstack/react-router'
import { Button, Container, Stack, Text } from '@sami/ui'

export function NoCompanyPage() {
  const { logout } = useRouteContext({ from: '/no-company' })
  return (
    <Container size="xs" py="xl">
      <Stack align="flex-start">
        <Text>No company assigned. Ask an administrator.</Text>
        <Button onClick={logout}>Sign out</Button>
      </Stack>
    </Container>
  )
}
