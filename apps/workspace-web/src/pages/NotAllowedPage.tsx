import { Link } from '@tanstack/react-router'
import { Container, Stack, Text, Title } from '@sami/ui'

export function NotAllowedPage() {
  return (
    <Container py="xl">
      <Stack>
        <Title order={2}>Not allowed</Title>
        <Text>Your account does not have access to that page.</Text>
        <Link to="/">Back to home</Link>
      </Stack>
    </Container>
  )
}
