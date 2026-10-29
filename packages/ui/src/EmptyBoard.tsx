import { Button, Stack, Text, ThemeIcon, Title } from '@mantine/core'
import { PencilSimpleIcon, PlusIcon, SquaresFourIcon } from '@phosphor-icons/react'

type EmptyBoardProps = { editing: boolean; onEdit: () => void; onAdd: () => void }

export function EmptyBoard({ editing, onEdit, onAdd }: EmptyBoardProps) {
  return (
    <Stack align="center" gap="xs" py={64} ta="center">
      <ThemeIcon size={72} radius="xl" variant="light">
        <SquaresFourIcon size={36} weight="duotone" />
      </ThemeIcon>
      <Title order={3} mt="sm">
        This board is empty
      </Title>
      <Text c="dimmed" maw={360}>
        Add widgets and build your own dashboard in your style
      </Text>
      {editing ? (
        <Button mt="sm" leftSection={<PlusIcon size={16} />} onClick={onAdd}>
          Add widget
        </Button>
      ) : (
        <Button mt="sm" variant="light" leftSection={<PencilSimpleIcon size={16} />} onClick={onEdit}>
          Edit board
        </Button>
      )}
    </Stack>
  )
}
