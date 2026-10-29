import './charts.css'
import { cell, defineChart } from '@tanstack/charts'
import { scaleBand } from '@tanstack/charts/scales/band'
import { tooltip } from '@tanstack/charts/tooltip'
import { useMemo } from 'react'
import { ChartCard } from './ChartCard'
import { formatCompact } from './format'
import type { ValueFormat } from './format'
import classes from './Heatmap.module.css'

export type HeatmapCell = { row: string; column: string; value: number }
export type HeatmapChartProps = { cells: HeatmapCell[]; title?: string; valueFormat?: ValueFormat }

const ROW_HEIGHT = 32
const AXIS_HEIGHT = 48
const MIN_HEIGHT = 160
const LEVELS = 8
const FLOOR = 12

const steps = Array.from({ length: LEVELS }, (_, step) => String(step))
const shade = (step: number) => `color-mix(in srgb, var(--ts-chart-1) ${Math.round(FLOOR + (step / (LEVELS - 1)) * (100 - FLOOR))}%, transparent)`

const unique = (values: string[]) => [...new Set(values)]

function heatmapDefinition(cells: HeatmapCell[], low: number, high: number) {
  const span = high - low
  const level = (value: number) => (span === 0 ? LEVELS - 3 : Math.min(LEVELS - 1, Math.floor(((value - low) / span) * LEVELS)))
  const shaded = cells.map((point) => ({ ...point, level: String(level(point.value)) }))
  return defineChart({
    marks: [cell(shaded, { x: 'column', y: 'row', color: 'level', inset: 1, radius: 4 })],
    scales: {
      x: { scale: () => scaleBand<string>().padding(0.04) },
      y: { scale: () => scaleBand<string>().padding(0.04) },
    },
    color: { domain: steps, range: steps.map((step) => shade(Number(step))) },
    tooltip,
  })
}

export function HeatmapChart({ cells, title, valueFormat }: HeatmapChartProps) {
  const values = cells.map((point) => point.value)
  const low = Math.min(...values)
  const high = Math.max(...values)
  const definition = useMemo(() => (cells.length > 0 ? heatmapDefinition(cells, low, high) : undefined), [cells, low, high])
  const rows = unique(cells.map((point) => point.row)).length
  return (
    <ChartCard
      title={title}
      empty={cells.length === 0}
      definition={definition}
      label="heatmap"
      height={Math.max(MIN_HEIGHT, rows * ROW_HEIGHT + AXIS_HEIGHT)}
      footer={
        <div className={classes.legend}>
          <span>{formatCompact(low, valueFormat)}</span>
          <span className={classes.ramp} aria-hidden />
          <span>{formatCompact(high, valueFormat)}</span>
        </div>
      }
    />
  )
}
