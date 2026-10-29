import { formatCompact } from './format'
import type { ValueFormat } from './format'
import classes from './Heatmap.module.css'

export function HeatLegend({ low, high, valueFormat }: { low: number; high: number; valueFormat?: ValueFormat }) {
  return (
    <div className={classes.legend}>
      <span>{formatCompact(low, valueFormat)}</span>
      <span className={classes.ramp} aria-hidden />
      <span>{formatCompact(high, valueFormat)}</span>
    </div>
  )
}
