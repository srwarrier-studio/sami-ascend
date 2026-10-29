import { Link } from '@tanstack/react-router'
import { Container, PageHeader, Text } from '@sami/ui'

export function NotFoundPage() {
  return (
    <Container py="xl">
      <PageHeader title="Page not found" />
      <Text>There is nothing at this address.</Text>
      <Link to="/">Back to my boards</Link>
    </Container>
  )
}
