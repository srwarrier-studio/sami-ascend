import { ActionIcon, Group, Popover, Stack, Text, Title } from '@mantine/core'
import { InfoIcon } from '@phosphor-icons/react'
import type { Help } from './help'

type WidgetTitleProps = { title?: string; help: Help; info?: string; label?: boolean }

export function WidgetTitle({ title, help, info, label }: WidgetTitleProps) {
  if (!title) return null
  return (
    <Group gap={4} wrap="nowrap">
      {label ? <Text c="dimmed">{title}</Text> : <Title order={4}>{title}</Title>}
      <Popover width={280} position="bottom-start" withArrow shadow="md">
        <Popover.Target>
          <ActionIcon variant="subtle" color="gray" size={24} radius="xl" aria-label={`About ${title}`}>
            <InfoIcon size={16} />
          </ActionIcon>
        </Popover.Target>
        <Popover.Dropdown>
          <Stack gap="xs">
            <div>
              <Text size="sm" fw={600}>
                What it shows
              </Text>
              <Text size="sm" c="dimmed">
                {info ?? help.shows}
              </Text>
            </div>
            <div>
              <Text size="sm" fw={600}>
                How to read it
              </Text>
              <Text size="sm" c="dimmed">
                {help.read}
              </Text>
            </div>
          </Stack>
        </Popover.Dropdown>
      </Popover>
    </Group>
  )
}
