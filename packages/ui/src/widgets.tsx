import { Card, Group, Stack, Table, Text, Title } from '@mantine/core'
import { ArrowDownIcon, ArrowUpIcon } from '@phosphor-icons/react'
import { formatDelta, formatValue } from './format'
import { Sparkline } from './Sparkline'
import type { ValueFormat } from './format'

export type KpiCardProps = {
  title: string
  value: number
  valueFormat?: ValueFormat
  delta?: number
  caption?: string
  trend?: number[]
}

export function KpiCard({ title, value, valueFormat, delta, caption, trend }: KpiCardProps) {
  const rising = delta !== undefined && delta >= 0
  const Arrow = rising ? ArrowUpIcon : ArrowDownIcon
  return (
    <Card>
      <Text c="dimmed">{title}</Text>
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
}

export function RankedList({ title, items, valueFormat }: RankedListProps) {
  return (
    <Card>
      <Title order={4}>{title}</Title>
      {items.length === 0 ? (
        <Text c="dimmed">No data</Text>
      ) : (
        <Stack>
          {items.map((item, index) => (
            <Group key={item.label} justify="space-between">
              <Text>{`${index + 1}. ${item.label}`}</Text>
              <Text fw={600}>{formatValue(item.value, valueFormat)}</Text>
            </Group>
          ))}
        </Stack>
      )}
    </Card>
  )
}

export type DataTableColumn = { key: string; label: string; format?: ValueFormat | 'text' }

export type DataTableProps = {
  title?: string
  columns: DataTableColumn[]
  rows: Record<string, string | number | null>[]
}

function cell(value: string | number | null | undefined, format: DataTableColumn['format']) {
  if (value === null || value === undefined) return ''
  if (typeof value === 'number' && format && format !== 'text') return formatValue(value, format)
  return String(value)
}

export function DataTable({ title, columns, rows }: DataTableProps) {
  return (
    <Card>
      {title && <Title order={4}>{title}</Title>}
      {rows.length === 0 ? (
        <Text c="dimmed">No data</Text>
      ) : (
        <Table>
          <Table.Thead>
            <Table.Tr>
              {columns.map((column) => (
                <Table.Th key={column.key}>{column.label}</Table.Th>
              ))}
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {rows.map((row, index) => (
              <Table.Tr key={index}>
                {columns.map((column) => (
                  <Table.Td key={column.key}>{cell(row[column.key], column.format)}</Table.Td>
                ))}
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}
    </Card>
  )
}
