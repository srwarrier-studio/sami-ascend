import './charts.css'
import { areaY, barY, colorLegend, colorLegendItems, defineChart, dot, group, lineY, stack, text } from '@tanstack/charts'
import { scaleBand } from '@tanstack/charts/scales/band'
import { scaleLinear } from '@tanstack/charts/scales/linear'
import { scalePoint } from '@tanstack/charts/scales/point'
import { tooltip } from '@tanstack/charts/tooltip'
import { useMemo } from 'react'
import { ChartCard } from './ChartCard'
import { CHART_MIN_HEIGHT } from './sizes'
import { helpText } from './help'
import { formatCompact, formatValue } from './format'
import type { ValueFormat } from './format'

export type ChartPointData = { label: string; value: number }

export type ChartProps = {
  data: ChartPointData[]
  title?: string
  info?: string
  measure?: string
  valueFormat?: ValueFormat
  xLabel?: string
  yLabel?: string
}

export type BarChartProps = ChartProps & { valueLabels?: boolean }

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
  xLabel?: string
  yLabel?: string
}

const CHART_HEIGHT = CHART_MIN_HEIGHT
const BAR_RADIUS = 6
const LINE_WIDTH = 2.5
const LATEST_RADIUS = 5
const LABEL_OFFSET = -8
const LABEL_SIZE = 11
const MAX_LABELLED_BARS = 16

export const tooltipFor = (xLabel = 'Period', yLabel = 'Value', valueFormat?: ValueFormat) => ({
  use: tooltip,
  items: [
    { channel: 'x' as const, label: xLabel },
    {
      channel: 'y' as const,
      label: yLabel,
      text: (point: { yValue: unknown }) => (typeof point.yValue === 'number' ? formatValue(point.yValue, valueFormat) : String(point.yValue)),
    },
  ],
})

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

function lineDefinition({ data, valueFormat, compare = [], label = 'This period', compareLabel = 'Previous period', xLabel, yLabel }: LineChartProps) {
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
    tooltip: tooltipFor(xLabel, yLabel, valueFormat),
  })
}

function barDefinition({ data, valueFormat, xLabel, yLabel, valueLabels = true }: BarChartProps) {
  const last = data[data.length - 1]
  const labelled = valueLabels && data.length <= MAX_LABELLED_BARS
  return defineChart({
    marks: [
      barY(data, {
        x: 'label',
        y: 'value',
        radius: { end: BAR_RADIUS },
        fill: (point) => (point === last ? 'var(--ts-chart-1)' : 'color-mix(in srgb, var(--ts-chart-1) 35%, transparent)'),
      }),
      ...(labelled ? [text(data, { x: 'label', y: 'value', text: (point) => formatCompact(point.value, valueFormat === 'currency' ? 'number' : valueFormat, true), dy: LABEL_OFFSET, fontSize: LABEL_SIZE })] : []),
    ],
    scales: scales('bar', valueFormat),
    tooltip: tooltipFor(xLabel, yLabel, valueFormat),
  })
}

const legend = { legend: colorLegend({ items: colorLegendItems({ justify: 'start' }) }) }

function areaDefinition({ data, valueFormat, xLabel, yLabel }: ChartProps) {
  const options = { x: 'label', y: 'value', color: 'series' } as const
  const rows = data.map((point) => ({ ...point, series: 'value' }))
  return defineChart({
    marks: [areaY(rows, { ...options, fillOpacity: 0.28 }), lineY(rows, { ...options, strokeWidth: 2 })],
    scales: scales('line', valueFormat),
    tooltip: tooltipFor(xLabel, yLabel, valueFormat),
  })
}

function stackedDefinition({ series, layout = 'stacked', valueFormat, xLabel, yLabel }: StackedBarChartProps) {
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
    tooltip: tooltipFor(xLabel, yLabel, valueFormat),
  })
}

export function LineChart({ data, title, info, measure, valueFormat, compare, label, compareLabel, xLabel, yLabel }: LineChartProps) {
  const definition = useMemo(
    () => lineDefinition({ data, valueFormat, compare, label, compareLabel, xLabel, yLabel: yLabel ?? title }),
    [data, valueFormat, compare, label, compareLabel, xLabel, yLabel, title],
  )
  return <ChartCard title={title} help={helpText('LineChart', measure)} info={info} empty={data.length === 0} definition={definition} label="line chart" height={CHART_HEIGHT} />
}

export function BarChart({ data, title, info, measure, valueFormat, xLabel, yLabel, valueLabels }: BarChartProps) {
  const definition = useMemo(() => barDefinition({ data, valueFormat, xLabel, yLabel: yLabel ?? title, valueLabels }), [data, valueFormat, xLabel, yLabel, title, valueLabels])
  return <ChartCard title={title} help={helpText('BarChart', measure)} info={info} empty={data.length === 0} definition={definition} label="bar chart" height={CHART_HEIGHT} />
}

export function AreaChart({ data, title, info, measure, valueFormat, xLabel, yLabel }: ChartProps) {
  const definition = useMemo(() => areaDefinition({ data, valueFormat, xLabel, yLabel: yLabel ?? title }), [data, valueFormat, xLabel, yLabel, title])
  return <ChartCard title={title} help={helpText('AreaChart', measure)} info={info} empty={data.length === 0} definition={definition} label="area chart" height={CHART_HEIGHT} />
}

export function StackedBarChart({ series, layout, title, info, measure, valueFormat, xLabel, yLabel }: StackedBarChartProps) {
  const definition = useMemo(() => stackedDefinition({ series, layout, valueFormat, xLabel, yLabel: yLabel ?? title }), [series, layout, valueFormat, xLabel, yLabel, title])
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
