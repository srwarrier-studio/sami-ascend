import './charts.css'
import { Chart } from '@tanstack/charts/react'
import { Box, Card, Text } from '@mantine/core'
import { useElementSize } from '@mantine/hooks'
import type { ComponentProps, ReactNode } from 'react'
import type { HelpText } from './help'
import { WidgetTitle } from './WidgetTitle'
import classes from './Widgets.module.css'

type ChartCardProps = {
  title?: string
  help: HelpText
  info?: string
  empty: boolean
  definition?: ComponentProps<typeof Chart>['definition']
  label: string
  height: number
  footer?: ReactNode
}

const INITIAL_WIDTH = 640

export function ChartCard({ title, help, info, empty, definition, label, height, footer }: ChartCardProps) {
  const { ref, height: measured } = useElementSize()
  return (
    <Card className={classes.card}>
      <WidgetTitle title={title} help={help} info={info} />
      {empty || !definition ? (
        <Text c="dimmed">No data</Text>
      ) : (
        <>
          <Box ref={ref} className={`${classes.chartBody} sami-chart`} mih={height}>
            <div className={classes.chartFill}>
              <Chart definition={definition} height={Math.max(measured, height)} initialWidth={INITIAL_WIDTH} ariaLabel={title ?? label} />
            </div>
          </Box>
          {footer}
        </>
      )}
    </Card>
  )
}
