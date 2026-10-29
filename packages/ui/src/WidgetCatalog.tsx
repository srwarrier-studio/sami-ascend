import { Button, Card, Group, Stack, Text } from '@mantine/core'
import { PlusIcon } from '@phosphor-icons/react'
import { registry } from './registry'

export function WidgetCatalog({ onPick, names = registry.names() }: { onPick: (name: string) => void; names?: string[] }) {
  const described = registry.describe().filter((entry) => names.includes(entry.name))
  return (
    <Stack gap="xs">
      {described.map((entry) => (
        <Card key={entry.name} padding="sm" radius="md">
          <Group justify="space-between" wrap="nowrap">
            <div>
              <Text fw={600}>{entry.name}</Text>
              <Text size="sm" c="dimmed">
                {entry.description}
              </Text>
            </div>
            <Button size="xs" variant="light" leftSection={<PlusIcon size={14} />} onClick={() => onPick(entry.name)} aria-label={`Add ${entry.name}`}>
              Add
            </Button>
          </Group>
        </Card>
      ))}
    </Stack>
  )
}
