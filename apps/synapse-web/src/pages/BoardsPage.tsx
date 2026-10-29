import { Container, PageHeader, Text } from '@sami/ui'

export function BoardsPage() {
  return (
    <>
      <PageHeader title="My boards" />
      <Container py="md">
        <Text c="dimmed">Your boards will appear here.</Text>
      </Container>
    </>
  )
}
