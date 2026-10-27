import { Card, Text } from '@mantine/core'
import type { ReactElement } from 'react'
import { z } from 'zod'
import { BarChart, LineChart } from './charts'
import { DataTable, KpiCard, RankedList } from './widgets'

const valueFormat = z.enum(['number', 'currency', 'percent']).optional()
const point = z.object({ label: z.string(), value: z.number() })

type Size = { minW: number; minH: number; defaultW: number; defaultH: number }

type Entry = {
  description: string
  schema: z.ZodType
  size: Size
  component: (props: never) => ReactElement
}

const entries: Record<string, Entry> = {
  KpiCard: {
    description: 'One headline number with an optional change versus the previous period (a fraction, 0.05 is +5%).',
    schema: z.object({
      title: z.string(),
      value: z.number(),
      valueFormat,
      delta: z.number().optional(),
      caption: z.string().optional(),
    }),
    size: { minW: 2, minH: 2, defaultW: 3, defaultH: 2 },
    component: KpiCard,
  },
  RankedList: {
    description: 'Items ranked from highest to lowest value, such as top customers or materials.',
    schema: z.object({ title: z.string(), items: z.array(point), valueFormat }),
    size: { minW: 3, minH: 3, defaultW: 4, defaultH: 4 },
    component: RankedList,
  },
  DataTable: {
    description: 'A table of rows, such as recent high-value sales. Each column picks a key from the rows.',
    schema: z.object({
      title: z.string().optional(),
      columns: z.array(
        z.object({
          key: z.string(),
          label: z.string(),
          format: z.enum(['text', 'number', 'currency', 'percent']).optional(),
        }),
      ),
      rows: z.array(z.record(z.string(), z.union([z.string(), z.number(), z.null()]))),
    }),
    size: { minW: 4, minH: 3, defaultW: 6, defaultH: 4 },
    component: DataTable,
  },
  LineChart: {
    description: 'A line over ordered labels, such as sales per day or per month.',
    schema: z.object({ data: z.array(point), title: z.string().optional(), valueFormat }),
    size: { minW: 4, minH: 3, defaultW: 6, defaultH: 4 },
    component: LineChart,
  },
  BarChart: {
    description: 'Bars per label, such as sales by customer or by material.',
    schema: z.object({ data: z.array(point), title: z.string().optional(), valueFormat }),
    size: { minW: 4, minH: 3, defaultW: 6, defaultH: 4 },
    component: BarChart,
  },
}

export function FallbackCard({ name }: { name: string }) {
  return (
    <Card>
      <Text c="dimmed">{`Cannot show widget ${name}`}</Text>
    </Card>
  )
}

export const registry = {
  names(): string[] {
    return Object.keys(entries)
  },

  describe() {
    return Object.entries(entries).map(([name, entry]) => ({
      name,
      description: entry.description,
      schema: z.toJSONSchema(entry.schema),
      size: entry.size,
    }))
  },

  render(name: string, props: unknown): ReactElement {
    const entry = Object.hasOwn(entries, name) ? entries[name] : undefined
    const parsed = entry?.schema.safeParse(props)
    if (!entry || !parsed?.success) return <FallbackCard name={name} />
    const Component = entry.component as (props: unknown) => ReactElement
    return <Component {...(parsed.data as object)} />
  },
}
