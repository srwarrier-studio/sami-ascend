import { SimpleGrid, Skeleton, Stack } from '@sami/ui'

const KPI_HEIGHT = 144
const CHART_HEIGHT = 288

export function BoardsSkeleton() {
  return (
    <Stack p="md" role="status" aria-label="Loading boards">
      <Skeleton height={12} width={80} />
      <Skeleton height={32} width={220} />
      <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }}>
        {[0, 1, 2, 3].map((index) => (
          <Skeleton key={index} height={KPI_HEIGHT} radius="lg" />
        ))}
      </SimpleGrid>
      <SimpleGrid cols={{ base: 1, lg: 2 }}>
        {[0, 1].map((index) => (
          <Skeleton key={index} height={CHART_HEIGHT} radius="lg" />
        ))}
      </SimpleGrid>
    </Stack>
  )
}
