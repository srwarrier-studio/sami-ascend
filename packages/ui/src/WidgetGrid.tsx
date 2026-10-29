import type { HTMLAttributes, ReactNode } from 'react'
import { registry } from './registry'
import { sizes } from './sizes'
import type { SizeName } from './sizes'
import classes from './WidgetGrid.module.css'

export function WidgetGrid({ children }: { children: ReactNode }) {
  return <div className={classes.grid}>{children}</div>
}

type WidgetCellProps = HTMLAttributes<HTMLDivElement> & {
  widget: string
  size?: SizeName
  editing?: boolean
  dragging?: boolean
}

const allowed = new Map(registry.describe().map((entry) => [entry.name, entry.sizes]))

export const allowedSizes = (widget: string): SizeName[] => allowed.get(widget) ?? []

export function WidgetCell({ widget, size, editing, dragging, children, ...rest }: WidgetCellProps) {
  const { w, h } = sizes[size && allowedSizes(widget).includes(size) ? size : (allowedSizes(widget)[0] ?? 'medium')]
  return (
    <div
      {...rest}
      className={classes.cell}
      data-span={w}
      data-rows={h}
      data-editing={editing || undefined}
      data-dragging={dragging || undefined}
    >
      {children}
    </div>
  )
}
