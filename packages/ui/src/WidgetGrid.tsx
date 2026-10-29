import type { HTMLAttributes, ReactNode } from 'react'
import { registry } from './registry'
import classes from './WidgetGrid.module.css'

export function WidgetGrid({ children }: { children: ReactNode }) {
  return <div className={classes.grid}>{children}</div>
}

type WidgetCellProps = HTMLAttributes<HTMLDivElement> & {
  widget: string
  editing?: boolean
  dragging?: boolean
}

const defaults = new Map(registry.describe().map((entry) => [entry.name, entry.size]))

export function WidgetCell({ widget, editing, dragging, children, ...rest }: WidgetCellProps) {
  const size = defaults.get(widget)
  return (
    <div
      {...rest}
      className={classes.cell}
      data-span={size?.defaultW ?? 4}
      data-rows={size?.defaultH ?? 4}
      data-editing={editing || undefined}
      data-dragging={dragging || undefined}
    >
      {children}
    </div>
  )
}
