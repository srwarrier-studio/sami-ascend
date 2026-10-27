import { Link } from '@tanstack/react-router'
import { Container, Stack, Text, Title } from '@sami/ui'

export function NotFoundPage() {
  return (
    <Container py="xl">
      <Stack>
        <Title order={2}>Page not found</Title>
        <Text>There is nothing at this address.</Text>
        <Link to="/">Back to home</Link>
      </Stack>
    </Container>
  )
}
