import './charts.css'
import { defineChart } from '@tanstack/charts'
import { pie, polar, radialArc, radialText } from '@tanstack/charts/polar'
import { scaleLinear } from '@tanstack/charts/scales/linear'
import { Text } from '@mantine/core'
import { useMemo } from 'react'
import { ChartCard } from './ChartCard'
import { help } from './help'
import { formatValue } from './format'
import type { ValueFormat } from './format'
import classes from './PolarCharts.module.css'

export type Tone = 'positive' | 'caution' | 'negative' | 'neutral'
export type DonutSlice = { label: string; value: number; tone?: Tone }

export type DonutChartProps = { slices: DonutSlice[]; title?: string; info?: string }
export type GaugeChartProps = { value: number; target: number; title?: string; info?: string; valueFormat?: ValueFormat; caption?: string }

const DONUT_HEIGHT = 220
const GAUGE_HEIGHT = 180
const PALETTE_SIZE = 6
const SLICE_GAP = 0.03
const GAUGE_SWEEP = Math.PI * 0.75
const tones: Record<Tone, string> = {
  positive: 'var(--sami-positive)',
  caution: 'var(--sami-caution)',
  negative: 'var(--sami-negative)',
  neutral: 'var(--mantine-color-gray-5)',
}

const unitScales = { angle: { scale: scaleLinear().domain([0, 1]) }, radius: { scale: scaleLinear().domain([0, 1]) } }

const colorKey = (slice: DonutSlice, index: number) => slice.tone ?? String((index % PALETTE_SIZE) + 1)
const paint = (key: string) => (key in tones ? tones[key as Tone] : `var(--ts-chart-${key})`)
const total = (slices: DonutSlice[]) => slices.reduce((sum, slice) => sum + slice.value, 0)
const percent = (part: number, whole: number) => Math.round((part / whole) * 100)

function donutDefinition(slices: DonutSlice[]) {
  const sum = total(slices)
  const arcs = pie(slices, { value: 'value', gapAngle: SLICE_GAP })
  const main = slices.reduce((best, slice) => (slice.value > best.value ? slice : best), slices[0])
  return defineChart({
    marks: [
      polar({
        inset: 8,
        radiusRatio: 0.92,
        marks: [
          radialArc(arcs, { innerRadius: ({ radius }) => radius * 0.64, cornerRadius: 4, color: 'label', key: 'label' }),
          radialText([main], {
            angle: 0,
            radius: 0,
            text: () => `${percent(main.value, sum)}%`,
            key: 'label',
            fill: 'currentColor',
            fontSize: 26,
            fontWeight: 600,
          }),
        ],
        scales: unitScales,
      }),
    ],
    scales: { x: null, y: null },
    color: { domain: slices.map((slice) => slice.label), range: slices.map((slice, index) => paint(colorKey(slice, index))) },
  })
}

export function DonutChart({ slices, title, info }: DonutChartProps) {
  const sum = total(slices)
  const definition = useMemo(() => (sum > 0 ? donutDefinition(slices) : undefined), [slices, sum])
  return (
    <ChartCard
      title={title}
      help={help.DonutChart}
      info={info}
      empty={!definition}
      definition={definition}
      label="donut chart"
      height={DONUT_HEIGHT}
      footer={
        <ul className={classes.legend}>
          {slices.map((slice, index) => (
            <li key={slice.label}>
              <span className={classes.dot} data-color={colorKey(slice, index)} />
              <span className={classes.name}>{slice.label}</span>
              <b>{`${percent(slice.value, sum)}%`}</b>
            </li>
          ))}
        </ul>
      }
    />
  )
}

function gaugeDefinition(value: number, target: number) {
  const reached = Math.min(Math.max(value, 0), target)
  const arcs = pie(
    [
      { id: 'reached', value: reached },
      { id: 'remaining', value: target - reached },
    ],
    { value: 'value', startAngle: -GAUGE_SWEEP, endAngle: GAUGE_SWEEP },
  )
  const label = { id: 'reached', value: percent(value, target) }
  return defineChart({
    marks: [
      polar({
        radiusRatio: 0.9,
        scales: unitScales,
        marks: [
          radialArc(arcs, { innerRadius: ({ radius }) => radius * 0.74, cornerRadius: 999, color: 'id', key: 'id' }),
          radialText([label], {
            angle: 0,
            radius: 0,
            text: (row) => `${row.value}%`,
            key: 'id',
            fill: 'currentColor',
            fontSize: 26,
            fontWeight: 600,
          }),
        ],
      }),
    ],
    scales: { x: null, y: null },
    color: { domain: ['reached', 'remaining'], range: ['var(--ts-chart-1)', 'color-mix(in srgb, currentColor 12%, transparent)'] },
  })
}

export function GaugeChart({ value, target, title, info, valueFormat, caption }: GaugeChartProps) {
  const definition = useMemo(() => (target > 0 ? gaugeDefinition(value, target) : undefined), [value, target])
  return (
    <ChartCard
      title={title}
      help={help.GaugeChart}
      info={info}
      empty={!definition}
      definition={definition}
      label="gauge"
      height={GAUGE_HEIGHT}
      footer={
        <Text ta="center" c="dimmed">
          {`${formatValue(value, valueFormat)} of ${formatValue(target, valueFormat)}${caption ? ` ${caption}` : ''}`}
        </Text>
      }
    />
  )
}
