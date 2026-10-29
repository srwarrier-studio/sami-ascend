import './charts.css'
import { cell, defineChart } from '@tanstack/charts'
import { scaleBand } from '@tanstack/charts/scales/band'
import { tooltip } from '@tanstack/charts/tooltip'
import { useMemo } from 'react'
import { ChartCard } from './ChartCard'
import { helpText } from './help'
import { colorDomain, colorRange, levelOf } from './heat'
import { HeatLegend } from './HeatLegend'
import type { ValueFormat } from './format'

export type HeatmapCell = { row: string; column: string; value: number }
export type HeatmapChartProps = { cells: HeatmapCell[]; title?: string; info?: string; measure?: string; valueFormat?: ValueFormat }

const ROW_HEIGHT = 32
const AXIS_HEIGHT = 48
const MIN_HEIGHT = 160
const unique = (values: string[]) => [...new Set(values)]

function heatmapDefinition(cells: HeatmapCell[], low: number, high: number) {
  const shaded = cells.map((point) => ({ ...point, level: levelOf(point.value, low, high) }))
  return defineChart({
    marks: [cell(shaded, { x: 'column', y: 'row', color: 'level', inset: 1, radius: 4 })],
    scales: {
      x: { scale: () => scaleBand<string>().padding(0.04) },
      y: { scale: () => scaleBand<string>().padding(0.04) },
    },
    color: { domain: colorDomain, range: colorRange },
    tooltip,
  })
}

export function HeatmapChart({ cells, title, info, measure, valueFormat }: HeatmapChartProps) {
  const values = cells.map((point) => point.value)
  const low = Math.min(...values)
  const high = Math.max(...values)
  const definition = useMemo(() => (cells.length > 0 ? heatmapDefinition(cells, low, high) : undefined), [cells, low, high])
  const rows = unique(cells.map((point) => point.row)).length
  return (
    <ChartCard
      title={title}
      help={helpText('HeatmapChart', measure)}
      info={info}
      empty={cells.length === 0}
      definition={definition}
      label="heatmap"
      height={Math.max(MIN_HEIGHT, rows * ROW_HEIGHT + AXIS_HEIGHT)}
      footer={<HeatLegend low={low} high={high} valueFormat={valueFormat} />}
    />
  )
}
