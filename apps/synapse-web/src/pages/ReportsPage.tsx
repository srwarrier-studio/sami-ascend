import { useRouteContext } from '@tanstack/react-router'
import { Container, PageHeader, SimpleGrid } from '@sami/ui'
import { CatalogWidget } from '../catalog/CatalogWidget'

export function WidgetsPage() {
  const { catalog, catalogClient } = useRouteContext({ from: '/widgets' })
  return (
    <>
      <PageHeader title="Widgets" breadcrumb={['Catalog']} />
      <Container size="xl" py="md">
        <SimpleGrid cols={{ base: 1, md: 2, xl: 3 }}>
          {catalog.map((entry) => (
            <CatalogWidget key={entry.id} entry={entry} client={catalogClient} />
          ))}
        </SimpleGrid>
      </Container>
    </>
  )
}
