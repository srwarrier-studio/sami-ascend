import { Card, Group, Progress, Stack, Table, Text, Title } from '@mantine/core'
import { ArrowDownIcon, ArrowUpIcon } from '@phosphor-icons/react'
import { formatDelta, formatValue } from './format'
import { help } from './help'
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
}

export function KpiCard({ title, value, valueFormat, delta, caption, trend, info }: KpiCardProps) {
  const rising = delta !== undefined && delta >= 0
  const Arrow = rising ? ArrowUpIcon : ArrowDownIcon
  return (
    <Card>
      <WidgetTitle title={title} help={help.KpiCard} info={info} label />
      <Group justify="space-between" align="flex-end" wrap="nowrap">
        <Stack gap={0}>
          <Title order={2}>{formatValue(value, valueFormat)}</Title>
          {delta !== undefined && (
            <Group gap={4}>
              <Arrow size={14} weight="bold" color={rising ? 'var(--sami-positive)' : 'var(--sami-negative)'} aria-hidden />
              <Text c={rising ? 'var(--sami-positive)' : 'var(--sami-negative)'} fw={500}>
                {formatDelta(delta)}
              </Text>
            </Group>
          )}
          {caption && <Text c="dimmed">{caption}</Text>}
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
}

export function RankedList({ title, items, valueFormat, info }: RankedListProps) {
  const top = Math.max(0, ...items.map((item) => item.value))
  return (
    <Card>
      <WidgetTitle title={title} help={help.RankedList} info={info} />
      {items.length === 0 ? (
        <Text c="dimmed">No data</Text>
      ) : (
        <Stack gap="sm">
          {items.map((item, index) => (
            <Stack key={item.label} gap={4}>
              <Group justify="space-between">
                <Text>{`${index + 1}. ${item.label}`}</Text>
                <Text fw={600}>{formatValue(item.value, valueFormat)}</Text>
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
    <Card>
      <WidgetTitle title={title} help={help.DataTable} info={info} />
      {rows.length === 0 ? (
        <Text c="dimmed">No data</Text>
      ) : (
        <Table>
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
      )}
    </Card>
  )
}
