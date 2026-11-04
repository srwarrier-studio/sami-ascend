import { ArrowDownIcon, ArrowRightIcon, ArrowUpIcon, Badge, Card, Group, Progress, Stack, Text } from '@sami/ui'
import classes from './Findings.module.css'
import type { FindingItem, FindingsBlock as Findings } from './answerBlocks'

const COLORS = { up: 'teal', down: 'red', flat: 'gray' }
const ICONS = { up: ArrowUpIcon, down: ArrowDownIcon, flat: ArrowRightIcon }

const sentence = (phrase: string) => `${phrase.charAt(0).toUpperCase()}${phrase.slice(1)}`

function Item({ item }: { item: FindingItem }) {
  const Icon = ICONS[item.direction]
  return (
    <Card withBorder padding="sm">
      <Stack gap={6}>
        <Group justify="space-between" wrap="nowrap">
          <Stack gap={0}>
            <Text fw={600}>{item.name}</Text>
            <Text size="xs" c="dimmed">
              {item.role === 'offset' ? `Offset by ${item.dimension}` : `By ${item.dimension}`}
            </Text>
          </Stack>
          <Badge color={COLORS[item.direction]} variant="light" leftSection={<Icon size={12} />}>
            {item.changeText}
          </Badge>
        </Group>
        <Text size="sm">{[item.amountText, item.shareText].filter(Boolean).join(' · ')}</Text>
        {item.priceText && (
          <Text size="xs" c="dimmed">
            {item.priceText}
          </Text>
        )}
        {item.paths.map((path, index) => (
          <Stack key={index} gap={2} className={classes.path}>
            {path.map((step, stepIndex) => (
              <Text key={stepIndex} size="xs">
                {stepIndex === 0 ? `Coincided with: ${step}` : `Behind that: ${step}`}
              </Text>
            ))}
          </Stack>
        ))}
      </Stack>
    </Card>
  )
}

export function FindingsBlock({ block }: { block: Findings }) {
  return (
    <Stack gap="sm">
      <Text fw={600}>{block.headline}</Text>
      {block.items.map((item, index) => (
        <Item key={`${item.name}-${index}`} item={item} />
      ))}
      <Stack gap={4}>
        <Progress value={block.coverage.explainedPercent} size="sm" radius="xl" aria-label="Share of the change explained" />
        <Text size="sm">{sentence(block.coverage.text)}</Text>
      </Stack>
      {block.notes.map((note, index) => (
        <Text key={index} size="xs" c="dimmed">
          {note}
        </Text>
      ))}
    </Stack>
  )
}
