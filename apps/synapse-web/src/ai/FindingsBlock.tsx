import type { ReactNode } from 'react'
import { ArrowDownIcon, ArrowRightIcon, ArrowUpIcon, Group, Progress, Stack, Text } from '@sami/ui'
import classes from './Findings.module.css'
import type { FindingItem, FindingsBlock as Findings } from './answerBlocks'

const ICONS = { up: ArrowUpIcon, down: ArrowDownIcon, flat: ArrowRightIcon }

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Stack gap="xs">
      <Text size="xs" fw={700} tt="uppercase" c="dimmed">
        {title}
      </Text>
      {children}
    </Stack>
  )
}

function Item({ item }: { item: FindingItem }) {
  const Icon = ICONS[item.direction]
  return (
    <Group gap="xs" wrap="nowrap" align="flex-start">
      <Icon size={16} weight="bold" className={`${classes.icon} ${classes[item.direction]}`} />
      <Stack gap={2}>
        <Text>
          <Text span fw={600}>
            {item.name}
          </Text>{' '}
          <Text span c="dimmed" size="sm">
            ({item.dimension})
          </Text>
        </Text>
        <Text size="sm">{item.detail}</Text>
        {item.priceText && (
          <Text size="sm" c="dimmed">
            {item.priceText}
          </Text>
        )}
        {item.reasons.map((reason, index) => (
          <Text key={index} size="sm" c="dimmed">
            {reason}
          </Text>
        ))}
      </Stack>
    </Group>
  )
}

export function FindingsBlock({ block }: { block: Findings }) {
  const movers = block.items.filter((item) => item.role === 'mover')
  const offsets = block.items.filter((item) => item.role === 'offset')
  return (
    <Stack gap="md">
      <Text fw={700} size="lg">
        {block.headline}
      </Text>
      {movers.length > 0 && (
        <Section title="What moved most">
          {movers.map((item, index) => (
            <Item key={`${item.name}-${index}`} item={item} />
          ))}
        </Section>
      )}
      {offsets.length > 0 && (
        <Section title="Partly offset by">
          {offsets.map((item, index) => (
            <Item key={`${item.name}-${index}`} item={item} />
          ))}
        </Section>
      )}
      <Section title="How much we can explain">
        <Progress value={block.coverage.explainedPercent} size="sm" radius="xl" aria-label="Share of the change explained" />
        <Text size="sm">{block.coverage.text}</Text>
      </Section>
      {block.notes.map((note, index) => (
        <Text key={index} size="xs" c="dimmed">
          {note}
        </Text>
      ))}
    </Stack>
  )
}
