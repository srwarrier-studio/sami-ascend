import './charts.css'
import { Chart } from '@tanstack/charts/react'
import { Card, Text } from '@mantine/core'
import type { ComponentProps, ReactNode } from 'react'
import type { Help } from './help'
import { WidgetTitle } from './WidgetTitle'

type ChartCardProps = {
  title?: string
  help: Help
  info?: string
  empty: boolean
  definition?: ComponentProps<typeof Chart>['definition']
  label: string
  height: number
  footer?: ReactNode
}

const INITIAL_WIDTH = 640

export function ChartCard({ title, help, info, empty, definition, label, height, footer }: ChartCardProps) {
  return (
    <Card>
      <WidgetTitle title={title} help={help} info={info} />
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
