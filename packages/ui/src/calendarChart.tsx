import './charts.css'
import { cell, defineChart } from '@tanstack/charts'
import type { ChartPoint, ChartValue } from '@tanstack/charts'
import { scaleBand } from '@tanstack/charts/scales/band'
import { tooltip } from '@tanstack/charts/tooltip'
import { useMemo } from 'react'
import { ChartCard } from './ChartCard'
import { formatValue } from './format'
import type { ValueFormat } from './format'
import { NONE, colorDomain, colorRange, levelOf } from './heat'
import { HeatLegend } from './HeatLegend'

export type CalendarDay = { date: string; value: number }
export type CalendarHeatmapChartProps = { days: CalendarDay[]; title?: string; valueFormat?: ValueFormat }

type Square = { week: string; weekday: string; date: string; value: number | undefined; level: string }

const DAY = 86400000
const ROW_HEIGHT = 18
const AXIS_HEIGHT = 40
const LABELLED_WEEKDAYS = ['Mon', 'Wed', 'Fri']
const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const MONTH_GAP = 3

const toTime = (iso: string) => Date.parse(`${iso}T00:00:00Z`)
const toIso = (time: number) => new Date(time).toISOString().slice(0, 10)
const weekdayOf = (time: number) => (new Date(time).getUTCDay() + 6) % 7

export function dayLabel(iso: string) {
  const time = toTime(iso)
  const date = new Date(time)
  return `${WEEKDAYS[weekdayOf(time)]} ${date.getUTCDate()} ${MONTHS[date.getUTCMonth()]} ${date.getUTCFullYear()}`
}

function squaresOf(days: CalendarDay[]) {
  const values = new Map(days.filter((day) => Number.isFinite(toTime(day.date))).map((day) => [day.date, day.value]))
  const times = [...values.keys()].map(toTime)
  if (times.length === 0) return { squares: [], low: 0, high: 0 }
  const present = [...values.values()]
  const low = Math.min(...present)
  const high = Math.max(...present)
  const squares: Square[] = []
  for (let time = Math.min(...times); time <= Math.max(...times); time += DAY) {
    const date = toIso(time)
    const weekday = weekdayOf(time)
    const value = values.get(date)
    squares.push({
      week: toIso(time - weekday * DAY),
      weekday: WEEKDAYS[weekday],
      date,
      value,
      level: value === undefined ? NONE : levelOf(value, low, high),
    })
  }
  return { squares, low, high }
}

function monthLabels(squares: Square[]) {
  const weeks = [...new Set(squares.map((square) => square.week))]
  const labels = new Map<string, string>()
  weeks.forEach((week) => {
    const first = squares.find((square) => square.week === week && square.date.endsWith('-01'))
    if (first) labels.set(week, MONTHS[Number(first.date.slice(5, 7)) - 1])
  })
  const start = squares[0]
  const nearest = weeks.findIndex((week) => labels.has(week))
  if (!labels.has(weeks[0]) && nearest >= MONTH_GAP) labels.set(weeks[0], MONTHS[Number(start.date.slice(5, 7)) - 1])
  return labels
}

function calendarDefinition(squares: Square[], valueFormat?: ValueFormat) {
  const labels = monthLabels(squares)
  const weeks = [...new Set(squares.map((square) => square.week))]
  return defineChart({
    marks: [cell(squares, { x: 'week', y: 'weekday', color: 'level', inset: 1.5, radius: 3 })],
    scales: {
      x: {
        scale: scaleBand<string>().domain(weeks).padding(0.05),
        side: 'top',
        axis: {
          ticks: { size: 0, format: (week: string) => labels.get(week) ?? '' },
          tickLabels: { thin: { keep: [...labels.keys()] } },
        },
      },
      y: {
        scale: scaleBand<string>().domain(WEEKDAYS).padding(0.05),
        axis: {
          ticks: { size: 0, format: (weekday: string) => (LABELLED_WEEKDAYS.includes(weekday) ? weekday : '') },
          tickLabels: { thin: { keep: LABELLED_WEEKDAYS } },
        },
      },
    },
    color: { domain: colorDomain, range: colorRange },
    tooltip: {
      use: tooltip,
      format: (point: ChartPoint<unknown, ChartValue, ChartValue>) => {
        const square = point.datum as Square
        return `${dayLabel(square.date)}: ${square.value === undefined ? 'No data' : formatValue(square.value, valueFormat)}`
      },
    },
  })
}

export function CalendarHeatmapChart({ days, title, valueFormat }: CalendarHeatmapChartProps) {
  const { squares, low, high } = useMemo(() => squaresOf(days), [days])
  const definition = useMemo(() => (squares.length > 0 ? calendarDefinition(squares, valueFormat) : undefined), [squares, valueFormat])
  return (
    <ChartCard
      title={title}
      empty={squares.length === 0}
      definition={definition}
      label="calendar heatmap"
      height={WEEKDAYS.length * ROW_HEIGHT + AXIS_HEIGHT}
      footer={<HeatLegend low={low} high={high} valueFormat={valueFormat} />}
    />
  )
}
