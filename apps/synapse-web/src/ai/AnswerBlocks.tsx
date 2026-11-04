import { Accordion, DataTable, LineChart, Stack, Text } from '@sami/ui'
import type { AnswerBlock, EvidenceBlock, TableBlock, TrendBlock } from './answerBlocks'
import { FindingsBlock } from './FindingsBlock'

const COLUMN_KEYS: Record<string, { key: string; format: 'text' | 'currency' | 'percent' }> = {
  Name: { key: 'name', format: 'text' },
  Current: { key: 'current', format: 'currency' },
  Previous: { key: 'previous', format: 'currency' },
  Change: { key: 'change', format: 'currency' },
  'Share of change': { key: 'share_percent', format: 'percent' },
  'Volume effect': { key: 'volume_effect', format: 'currency' },
  'Price effect': { key: 'price_effect', format: 'currency' },
}

const asNumber = (value: string | null | undefined, divisor = 1) => (value === null || value === undefined ? null : Number(value) / divisor)

function Trend({ block }: { block: TrendBlock }) {
  const marked = block.marked.length ? ` (${block.marked.join(' and ')} compared)` : ''
  return <LineChart title={`${block.metric.charAt(0).toUpperCase()}${block.metric.slice(1)}, last ${block.points.length} months${marked}`} measure={block.currency} valueFormat={/^[A-Z]{3}$/.test(block.currency) ? `currency:${block.currency}` : 'currency'} data={block.points.map((point) => ({ label: point.month, value: Number(point.value) }))} />
}

function Table({ block }: { block: TableBlock }) {
  const columns = block.columns.map((label) => ({ label, ...(COLUMN_KEYS[label] ?? { key: label, format: 'text' as const }) }))
  const rows = block.rows.map((row) =>
    Object.fromEntries(columns.map(({ key, format }) => [key, format === 'text' ? (row[key] ?? '') : asNumber(row[key], format === 'percent' ? 100 : 1)])),
  )
  return <DataTable title={block.title} columns={columns} rows={rows} />
}

function Evidence({ block }: { block: EvidenceBlock }) {
  return (
    <Stack gap={4}>
      <Text fw={600} size="sm">
        Evidence: {block.finding}
      </Text>
      <Accordion variant="contained">
        {block.steps.map((step, index) => (
          <Accordion.Item key={index} value={String(index)}>
            <Accordion.Control>{step.summary}</Accordion.Control>
            <Accordion.Panel>
              {step.rows.length === 0 && <Text size="sm" c="dimmed">No rows</Text>}
              {step.rows.map((row, rowIndex) => (
                <Text key={rowIndex} size="xs" mb={4}>
                  {Object.entries(row).map(([key, value]) => `${key}: ${String(value)}`).join(' · ')}
                </Text>
              ))}
            </Accordion.Panel>
          </Accordion.Item>
        ))}
      </Accordion>
    </Stack>
  )
}

function Block({ block }: { block: AnswerBlock }) {
  if (block.type === 'text') return <Stack gap={4}>{block.lines.map((line, index) => <Text key={index}>{line}</Text>)}</Stack>
  if (block.type === 'trend') return <Trend block={block} />
  if (block.type === 'table') return <Table block={block} />
  if (block.type === 'findings') return <FindingsBlock block={block} />
  return <Evidence block={block} />
}

export function AnswerBlocks({ blocks }: { blocks: AnswerBlock[] }) {
  return (
    <Stack gap="sm">
      {blocks.map((block, index) => <Block key={index} block={block} />)}
    </Stack>
  )
}
