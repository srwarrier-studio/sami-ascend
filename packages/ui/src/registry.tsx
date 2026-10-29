import { Card, Text } from '@mantine/core'
import type { ReactElement } from 'react'
import { z } from 'zod'
import { AreaChart, BarChart, LineChart, StackedBarChart } from './charts'
import { CalendarHeatmapChart } from './calendarChart'
import { HeatmapChart } from './heatmapChart'
import { DonutChart, GaugeChart } from './polarCharts'
import { helpText } from './help'
import type { WidgetName } from './help'
import { sized } from './sizes'
import type { SizeName } from './sizes'
import { DataTable, KpiCard, RankedList } from './widgets'

const valueFormat = z.enum(['number', 'currency', 'percent']).optional()
const point = z.object({ label: z.string(), value: z.number() })
const info = z.string().optional()
const measure = z.string().optional()

type Entry = {
  description: string
  schema: z.ZodType
  sizes: SizeName[]
  component: (props: never) => ReactElement
}

const entries: Record<string, Entry> = {
  KpiCard: {
    description:
      'One headline number with an optional change versus the previous period (a fraction, 0.05 is +5%) and an optional trend of recent values drawn as a sparkline.',
    schema: z.object({
      title: z.string(),
      info,
      measure,
      value: z.number(),
      valueFormat,
      delta: z.number().optional(),
      caption: z.string().optional(),
      trend: z.array(z.number()).optional(),
    }),
    sizes: ['kpi'],
    component: KpiCard,
  },
  RankedList: {
    description: 'Items ranked from highest to lowest value, such as top customers or materials.',
    schema: z.object({ title: z.string(), info, measure, items: z.array(point), valueFormat }),
    sizes: ['small', 'medium'],
    component: RankedList,
  },
  DataTable: {
    description: 'A table of rows, such as recent high-value sales. Each column picks a key from the rows.',
    schema: z.object({
      title: z.string().optional(),
      info,
      measure,
      columns: z.array(
        z.object({
          key: z.string(),
          label: z.string(),
          format: z.enum(['text', 'number', 'currency', 'percent', 'status']).optional(),
        }),
      ),
      rows: z.array(z.record(z.string(), z.union([z.string(), z.number(), z.null()]))),
    }),
    sizes: ['large'],
    component: DataTable,
  },
  LineChart: {
    description:
      'A line over ordered labels, such as sales per day or per month. An optional compare series shows the previous period behind it.',
    schema: z.object({
      data: z.array(point),
      compare: z.array(point).optional(),
      label: z.string().optional(),
      compareLabel: z.string().optional(),
      title: z.string().optional(),
      info,
      measure,
      valueFormat,
    }),
    sizes: ['medium', 'large'],
    component: LineChart,
  },
  AreaChart: {
    description: 'A filled trend over ordered labels, such as cumulative sales or volume per day.',
    schema: z.object({ data: z.array(point), title: z.string().optional(), info, measure, valueFormat }),
    sizes: ['medium', 'large'],
    component: AreaChart,
  },
  StackedBarChart: {
    description: 'Bars split into named parts, such as sales by status per month. Layout is stacked (default) or grouped side by side.',
    schema: z.object({
      series: z.array(z.object({ name: z.string(), data: z.array(point) })),
      layout: z.enum(['stacked', 'grouped']).optional(),
      title: z.string().optional(),
      info,
      measure,
      valueFormat,
    }),
    sizes: ['medium', 'large'],
    component: StackedBarChart,
  },
  HeatmapChart: {
    description: 'An intensity grid for a value over two named axes, such as sales by weekday and hour or by customer and month.',
    schema: z.object({
      cells: z.array(z.object({ row: z.string(), column: z.string(), value: z.number() })),
      title: z.string().optional(),
      info,
      measure,
      valueFormat,
    }),
    sizes: ['medium', 'large'],
    component: HeatmapChart,
  },
  CalendarHeatmapChart: {
    description: 'A year calendar with one cell per day, shaded by value, such as sales per day. Shows which months and days were busy or quiet. Dates are YYYY-MM-DD.',
    schema: z.object({
      days: z.array(z.object({ date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/), value: z.number() })),
      title: z.string().optional(),
      info,
      measure,
      valueFormat,
    }),
    sizes: ['large'],
    component: CalendarHeatmapChart,
  },
  DonutChart: {
    description: 'Shares of a whole, such as invoices by status. A slice may carry a tone: positive, caution, negative or neutral.',
    schema: z.object({
      title: z.string().optional(),
      info,
      measure,
      slices: z
        .array(z.object({ label: z.string(), value: z.number().nonnegative(), tone: z.enum(['positive', 'caution', 'negative', 'neutral']).optional() }))
        .refine((slices) => slices.reduce((sum, slice) => sum + slice.value, 0) > 0),
    }),
    sizes: ['small', 'medium'],
    component: DonutChart,
  },
  GaugeChart: {
    description: 'One value against a target as a progress ring, such as month-to-date sales against the monthly target.',
    schema: z.object({ title: z.string().optional(), info, measure, value: z.number(), target: z.number().positive(), valueFormat, caption: z.string().optional() }),
    sizes: ['small', 'medium'],
    component: GaugeChart,
  },
  BarChart: {
    description: 'Bars per label, such as sales by customer or by material.',
    schema: z.object({ data: z.array(point), title: z.string().optional(), info, measure, valueFormat }),
    sizes: ['medium', 'large'],
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
      size: sized(entry.sizes[0]),
      sizes: entry.sizes,
      help: helpText(name as WidgetName),
    }))
  },

  validate(name: string, props: unknown): boolean {
    return Object.hasOwn(entries, name) && entries[name].schema.safeParse(props).success
  },

  render(name: string, props: unknown): ReactElement {
    const entry = Object.hasOwn(entries, name) ? entries[name] : undefined
    const parsed = entry?.schema.safeParse(props)
    if (!entry || !parsed?.success) return <FallbackCard name={name} />
    const Component = entry.component as (props: unknown) => ReactElement
    return <Component {...(parsed.data as object)} />
  },
}
