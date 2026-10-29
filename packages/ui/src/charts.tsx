import './charts.css'
import { areaY, barY, colorLegend, colorLegendItems, defineChart, dot, group, lineY, stack } from '@tanstack/charts'
import { scaleBand } from '@tanstack/charts/scales/band'
import { scaleLinear } from '@tanstack/charts/scales/linear'
import { scalePoint } from '@tanstack/charts/scales/point'
import { tooltip } from '@tanstack/charts/tooltip'
import { useMemo } from 'react'
import { ChartCard } from './ChartCard'
import { CHART_MIN_HEIGHT } from './sizes'
import { helpText } from './help'
import { formatCompact } from './format'
import type { ValueFormat } from './format'

export type ChartPointData = { label: string; value: number }

export type ChartProps = {
  data: ChartPointData[]
  title?: string
  info?: string
  measure?: string
  valueFormat?: ValueFormat
}

export type LineChartProps = ChartProps & {
  compare?: ChartPointData[]
  label?: string
  compareLabel?: string
}

export type StackedSeries = { name: string; data: ChartPointData[] }

export type StackedBarChartProps = {
  series: StackedSeries[]
  layout?: 'stacked' | 'grouped'
  title?: string
  info?: string
  measure?: string
  valueFormat?: ValueFormat
}

const CHART_HEIGHT = CHART_MIN_HEIGHT
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
    ...(previous.length > 0 ? { color: legend } : {}),
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

const legend = { legend: colorLegend({ items: colorLegendItems({ justify: 'start' }) }) }

function areaDefinition({ data, valueFormat }: ChartProps) {
  const options = { x: 'label', y: 'value', color: 'series' } as const
  const rows = data.map((point) => ({ ...point, series: 'value' }))
  return defineChart({
    marks: [areaY(rows, { ...options, fillOpacity: 0.28 }), lineY(rows, { ...options, strokeWidth: 2 })],
    scales: scales('line', valueFormat),
    tooltip,
  })
}

function stackedDefinition({ series, layout = 'stacked', valueFormat }: StackedBarChartProps) {
  const rows = series.flatMap((part) => part.data.map((point) => ({ label: point.label, series: part.name, value: point.value })))
  return defineChart({
    marks: [
      barY(rows, {
        x: 'label',
        y: 'value',
        color: 'series',
        ...(layout === 'grouped'
          ? { layout: group(), radius: { end: BAR_RADIUS } }
          : { layout: stack(), radius: { end: BAR_RADIUS, stack: 'outer' as const } }),
      }),
    ],
    scales: scales('bar', valueFormat),
    color: legend,
    tooltip,
  })
}

export function LineChart({ data, title, info, measure, valueFormat, compare, label, compareLabel }: LineChartProps) {
  const definition = useMemo(
    () => lineDefinition({ data, valueFormat, compare, label, compareLabel }),
    [data, valueFormat, compare, label, compareLabel],
  )
  return <ChartCard title={title} help={helpText('LineChart', measure)} info={info} empty={data.length === 0} definition={definition} label="line chart" height={CHART_HEIGHT} />
}

export function BarChart({ data, title, info, measure, valueFormat }: ChartProps) {
  const definition = useMemo(() => barDefinition({ data, valueFormat }), [data, valueFormat])
  return <ChartCard title={title} help={helpText('BarChart', measure)} info={info} empty={data.length === 0} definition={definition} label="bar chart" height={CHART_HEIGHT} />
}

export function AreaChart({ data, title, info, measure, valueFormat }: ChartProps) {
  const definition = useMemo(() => areaDefinition({ data, valueFormat }), [data, valueFormat])
  return <ChartCard title={title} help={helpText('AreaChart', measure)} info={info} empty={data.length === 0} definition={definition} label="area chart" height={CHART_HEIGHT} />
}

export function StackedBarChart({ series, layout, title, info, measure, valueFormat }: StackedBarChartProps) {
  const definition = useMemo(() => stackedDefinition({ series, layout, valueFormat }), [series, layout, valueFormat])
  return (
    <ChartCard
      title={title}
      help={helpText('StackedBarChart', measure)}
      info={info}
      empty={series.every((part) => part.data.length === 0)}
      definition={definition}
      label="stacked bar chart"
      height={CHART_HEIGHT}
    />
  )
}
