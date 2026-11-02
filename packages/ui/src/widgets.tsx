import { Card, Group, Progress, Stack, Table, Text, Title } from '@mantine/core'
import { ArrowDownIcon, ArrowUpIcon } from '@phosphor-icons/react'
import { formatDelta, formatValue } from './format'
import { helpText } from './help'
import { Sparkline } from './Sparkline'
import { statusTone } from './status'
import { WidgetTitle } from './WidgetTitle'
import classes from './Widgets.module.css'
import type { ValueFormat } from './format'

export type KpiCardProps = {
  title: string
  value: number
  valueFormat?: ValueFormat
  delta?: number
  caption?: string
  trend?: number[]
  info?: string
  measure?: string
  note?: string
  partial?: boolean
  asOf?: string
}

export const ATTENTION_FALL = 0.1

export const clockTime = (iso: string) => {
  const time = new Date(iso)
  return Number.isNaN(time.getTime()) ? null : time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export function AsOf({ at }: { at?: string }) {
  const time = at ? clockTime(at) : null
  return time ? (
    <Text size="xs" c="dimmed" ta="right" className={classes.asOf}>
      {`as of ${time}`}
    </Text>
  ) : null
}

export function KpiCard({ title, value, valueFormat, delta, caption, trend, info, measure, note, partial, asOf }: KpiCardProps) {
  const rising = delta !== undefined && delta >= 0
  const Arrow = rising ? ArrowUpIcon : ArrowDownIcon
  const needsAttention = delta !== undefined && !partial && delta < -ATTENTION_FALL
  const tone = needsAttention ? 'var(--sami-negative)' : 'var(--mantine-color-dimmed)'
  return (
    <Card className={classes.card}>
      <Group justify="space-between" wrap="nowrap" gap="xs">
        <WidgetTitle title={title} help={helpText('KpiCard', measure)} info={info} label />
        <AsOf at={asOf} />
      </Group>
      <Group className={classes.kpiBody} justify="space-between" align="flex-end" wrap="nowrap">
        <Stack gap={0}>
          <Title order={2}>{formatValue(value, valueFormat)}</Title>
          {delta === undefined ? (
            <Text aria-hidden className={classes.spacer}>
              &nbsp;
            </Text>
          ) : (
            <Group gap={4}>
              <Arrow size={14} weight="bold" color={tone} aria-hidden />
              <Text c={tone} fw={500}>
                {formatDelta(delta)}
              </Text>
            </Group>
          )}
          {caption && <Text c="dimmed">{caption}</Text>}
          {note && (
            <Text size="xs" c="dimmed">
              {note}
            </Text>
          )}
        </Stack>
        {trend && trend.length > 1 && <Sparkline values={trend} />}
      </Group>
    </Card>
  )
}

export type RankedListProps = {
  title: string
  items: { label: string; value: number }[]
  valueFormat?: ValueFormat
  info?: string
  measure?: string
}

export function RankedList({ title, items, valueFormat, info, measure }: RankedListProps) {
  const top = Math.max(0, ...items.map((item) => item.value))
  return (
    <Card className={classes.card}>
      <WidgetTitle title={title} help={helpText('RankedList', measure)} info={info} />
      {items.length === 0 ? (
        <Text c="dimmed">No data</Text>
      ) : (
        <Stack className={classes.body} gap="sm">
          {items.map((item, index) => (
            <Stack key={item.label} gap={4}>
              <Group justify="space-between" wrap="nowrap" gap="xs">
                <Text flex={1} miw={0} truncate="end" title={item.label}>{`${index + 1}. ${item.label}`}</Text>
                <Text fw={600} flex="none">
                  {formatValue(item.value, valueFormat)}
                </Text>
              </Group>
              <Progress value={top > 0 ? (Math.max(0, item.value) / top) * 100 : 0} size="xs" radius="xl" aria-label={item.label} />
            </Stack>
          ))}
        </Stack>
      )}
    </Card>
  )
}

export type DataTableColumn = { key: string; label: string; format?: ValueFormat | 'text' | 'status' }

export type DataTableProps = {
  title?: string
  info?: string
  columns: DataTableColumn[]
  rows: Record<string, string | number | null>[]
}

const isNumeric = (format: DataTableColumn['format']) => format === 'number' || format === 'currency' || format === 'percent'

function cell(value: string | number | null | undefined, format: DataTableColumn['format']) {
  if (value === null || value === undefined) return ''
  if (format === 'status') return <span className={classes.pill} data-tone={statusTone(String(value))}>{String(value)}</span>
  if (typeof value === 'number' && format && format !== 'text') return formatValue(value, format)
  return String(value)
}

export function DataTable({ title, info, columns, rows }: DataTableProps) {
  return (
    <Card className={classes.card}>
      <WidgetTitle title={title} help={helpText('DataTable')} info={info} />
      {rows.length === 0 ? (
        <Text c="dimmed">No data</Text>
      ) : (
        <div className={classes.body}>
        <Table stickyHeader>
          <Table.Thead>
            <Table.Tr>
              {columns.map((column) => (
                <Table.Th key={column.key} ta={isNumeric(column.format) ? 'right' : undefined}>
                  {column.label}
                </Table.Th>
              ))}
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {rows.map((row, index) => (
              <Table.Tr key={index}>
                {columns.map((column) => (
                  <Table.Td key={column.key} ta={isNumeric(column.format) ? 'right' : undefined}>
                    {cell(row[column.key], column.format)}
                  </Table.Td>
                ))}
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
        </div>
      )}
    </Card>
  )
}
