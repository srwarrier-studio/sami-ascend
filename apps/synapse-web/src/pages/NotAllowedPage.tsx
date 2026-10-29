import { Container, PageHeader, Text } from '@sami/ui'

export function NotAllowedPage() {
  return (
    <Container py="xl">
      <PageHeader title="Not allowed" />
      <Text>Your account does not have access to Synapse. Ask an admin for the management role.</Text>
    </Container>
  )
}
