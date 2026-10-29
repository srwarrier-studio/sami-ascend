import { Button, Card, Group, Stack, Text } from '@sami/ui'
import { catalog } from '../catalog/catalog'

export function CatalogPicker({ onPick }: { onPick: (catalogId: string) => void }) {
  return (
    <Stack gap="xs">
      {catalog.map((entry) => (
        <Card key={entry.id} padding="sm" radius="md">
          <Group justify="space-between" wrap="nowrap">
            <div>
              <Text fw={600}>{entry.title}</Text>
              <Text size="sm" c="dimmed">
                {entry.description}
              </Text>
            </div>
            <Button size="xs" variant="light" onClick={() => onPick(entry.id)} aria-label={`Add ${entry.title}`}>
              Add
            </Button>
          </Group>
        </Card>
      ))}
    </Stack>
  )
}
