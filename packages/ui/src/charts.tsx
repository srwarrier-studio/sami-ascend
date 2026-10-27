import './charts.css'
import { barY, defineChart, lineY } from '@tanstack/charts'
import { Chart } from '@tanstack/charts/react'
import { scaleBand } from '@tanstack/charts/scales/band'
import { scaleLinear } from '@tanstack/charts/scales/linear'
import { scalePoint } from '@tanstack/charts/scales/point'
import { tooltip } from '@tanstack/charts/tooltip'
import { Card, Text, Title } from '@mantine/core'
import { useMemo } from 'react'
import { formatValue } from './format'
import type { ValueFormat } from './format'

export type ChartPointData = { label: string; value: number }

export type ChartProps = {
  data: ChartPointData[]
  title?: string
  valueFormat?: ValueFormat
}

const CHART_HEIGHT = 260
const INITIAL_WIDTH = 640

function ChartCard({ data, title, valueFormat, kind }: ChartProps & { kind: 'line' | 'bar' }) {
  const definition = useMemo(() => {
    const options = { x: 'label', y: 'value' } as const
    return defineChart({
      marks: [kind === 'line' ? lineY(data, options) : barY(data, options)],
      scales: {
        x: { scale: kind === 'line' ? () => scalePoint<string>().padding(0.4) : () => scaleBand().padding(0.2) },
        y: {
          scale: scaleLinear,
          nice: true,
          grid: true,
          axis: { ticks: { format: (value: number) => formatValue(value, valueFormat) } },
        },
      },
      tooltip,
    })
  }, [data, kind, valueFormat])

  return (
    <Card>
      {title && <Title order={4}>{title}</Title>}
      {data.length === 0 ? (
        <Text c="dimmed">No data</Text>
      ) : (
        <div className="sami-chart">
          <Chart
            definition={definition}
            height={CHART_HEIGHT}
            initialWidth={INITIAL_WIDTH}
            ariaLabel={title ?? `${kind} chart`}
          />
        </div>
      )}
    </Card>
  )
}

export function LineChart(props: ChartProps) {
  return <ChartCard {...props} kind="line" />
}

export function BarChart(props: ChartProps) {
  return <ChartCard {...props} kind="bar" />
}
