import { useRouteContext } from '@tanstack/react-router'
import { Container, PageHeader, SimpleGrid } from '@sami/ui'
import { CatalogWidget } from '../catalog/CatalogWidget'
import { catalog } from '../catalog/catalog'

export function WidgetsPage() {
  const { salesData } = useRouteContext({ from: '/widgets' })
  return (
    <>
      <PageHeader title="Widgets" breadcrumb={['Catalog']} />
      <Container size="xl" py="md">
        <SimpleGrid cols={{ base: 1, md: 2, xl: 3 }}>
          {catalog.map((entry) => (
            <CatalogWidget key={entry.id} entry={entry} data={salesData} />
          ))}
        </SimpleGrid>
      </Container>
    </>
  )
}
