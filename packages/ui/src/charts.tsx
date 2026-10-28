import './charts.css'
import { areaY, barY, colorLegend, colorLegendItems, defineChart, dot, lineY } from '@tanstack/charts'
import { Chart } from '@tanstack/charts/react'
import { scaleBand } from '@tanstack/charts/scales/band'
import { scaleLinear } from '@tanstack/charts/scales/linear'
import { scalePoint } from '@tanstack/charts/scales/point'
import { tooltip } from '@tanstack/charts/tooltip'
import { Card, Text, Title } from '@mantine/core'
import { useMemo } from 'react'
import { formatCompact } from './format'
import type { ValueFormat } from './format'

export type ChartPointData = { label: string; value: number }

export type ChartProps = {
  data: ChartPointData[]
  title?: string
  valueFormat?: ValueFormat
}

export type LineChartProps = ChartProps & {
  compare?: ChartPointData[]
  label?: string
  compareLabel?: string
}

const CHART_HEIGHT = 260
const INITIAL_WIDTH = 640
const BAR_RADIUS = 6
const LINE_WIDTH = 2.5
const LATEST_RADIUS = 5

function scales(kind: 'line' | 'bar', valueFormat?: ValueFormat) {
  return {
    x: { scale: kind === 'line' ? () => scalePoint<string>().padding(0.4) : () => scaleBand().padding(0.3) },
    y: {
      scale: scaleLinear,
      nice: true,
      grid: true,
      axis: { ticks: { format: (value: number) => formatCompact(value, valueFormat) } },
    },
  }
}

function lineDefinition({ data, valueFormat, compare = [], label = 'This period', compareLabel = 'Previous period' }: LineChartProps) {
  const main = data.map((point) => ({ ...point, series: label }))
  const previous = compare.map((point) => ({ ...point, series: compareLabel }))
  const options = { x: 'label', y: 'value', color: 'series' } as const
  return defineChart({
    marks: [
      areaY(main, { ...options, fillOpacity: 0.12 }),
      ...(previous.length > 0 ? [lineY(previous, { ...options, strokeWidth: 2 })] : []),
      lineY(main, { ...options, strokeWidth: LINE_WIDTH }),
      dot(main.slice(-1), { ...options, r: LATEST_RADIUS, stroke: 'var(--mantine-color-body)', strokeWidth: 2 }),
    ],
    scales: scales('line', valueFormat),
    ...(previous.length > 0 ? { color: { legend: colorLegend({ items: colorLegendItems({ justify: 'start' }) }) } } : {}),
    tooltip,
  })
}

function barDefinition({ data, valueFormat }: ChartProps) {
  const last = data[data.length - 1]
  return defineChart({
    marks: [
      barY(data, {
        x: 'label',
        y: 'value',
        radius: { end: BAR_RADIUS },
        fill: (point) => (point === last ? 'var(--ts-chart-1)' : 'color-mix(in srgb, var(--ts-chart-1) 35%, transparent)'),
      }),
    ],
    scales: scales('bar', valueFormat),
    tooltip,
  })
}

type Definition = ReturnType<typeof lineDefinition> | ReturnType<typeof barDefinition>

function ChartCard({ title, empty, definition, label }: { title?: string; empty: boolean; definition: Definition; label: string }) {
  return (
    <Card>
      {title && <Title order={4}>{title}</Title>}
      {empty ? (
        <Text c="dimmed">No data</Text>
      ) : (
        <div className="sami-chart">
          <Chart definition={definition} height={CHART_HEIGHT} initialWidth={INITIAL_WIDTH} ariaLabel={title ?? label} />
        </div>
      )}
    </Card>
  )
}

export function LineChart({ data, title, valueFormat, compare, label, compareLabel }: LineChartProps) {
  const definition = useMemo(
    () => lineDefinition({ data, valueFormat, compare, label, compareLabel }),
    [data, valueFormat, compare, label, compareLabel],
  )
  return <ChartCard title={title} empty={data.length === 0} definition={definition} label="line chart" />
}

export function BarChart({ data, title, valueFormat }: ChartProps) {
  const definition = useMemo(() => barDefinition({ data, valueFormat }), [data, valueFormat])
  return <ChartCard title={title} empty={data.length === 0} definition={definition} label="bar chart" />
}
