import './charts.css'
import { Chart } from '@tanstack/charts/react'
import { Card, Text, Title } from '@mantine/core'
import type { ComponentProps, ReactNode } from 'react'

type ChartCardProps = {
  title?: string
  empty: boolean
  definition?: ComponentProps<typeof Chart>['definition']
  label: string
  height: number
  footer?: ReactNode
}

const INITIAL_WIDTH = 640

export function ChartCard({ title, empty, definition, label, height, footer }: ChartCardProps) {
  return (
    <Card>
      {title && <Title order={4}>{title}</Title>}
      {empty || !definition ? (
        <Text c="dimmed">No data</Text>
      ) : (
        <div className="sami-chart">
          <Chart definition={definition} height={height} initialWidth={INITIAL_WIDTH} ariaLabel={title ?? label} />
          {footer}
        </div>
      )}
    </Card>
  )
}
