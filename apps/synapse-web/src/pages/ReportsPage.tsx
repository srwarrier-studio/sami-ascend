import { Container, PageHeader, Text, Title } from '@sami/ui'

export function ReportsPage() {
  return (
    <>
      <PageHeader title="Reports" breadcrumb={['Reports']} />
      <Container size="xl" py="xl">
        <Title order={3}>Coming soon</Title>
        <Text c="dimmed">Reports will appear here.</Text>
      </Container>
    </>
  )
}
