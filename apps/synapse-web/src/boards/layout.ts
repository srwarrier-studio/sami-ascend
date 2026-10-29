import { allowedSizes, arrange, widgetShape } from '@sami/ui'
import type { SizeName } from '@sami/ui'
import { catalog } from '../catalog/catalog'
import type { BoardWidget } from './boardStore'

export const MAX_WIDGETS = 15

export const addWidget = (widgets: BoardWidget[], catalogId: string): BoardWidget[] => [
  ...widgets,
  { id: `w-${crypto.randomUUID()}`, catalogId },
]

export const insertWidget = (widgets: BoardWidget[], catalogId: string, beforeId: string | null): BoardWidget[] => {
  const at = widgets.findIndex((widget) => widget.id === beforeId)
  if (at < 0) return addWidget(widgets, catalogId)
  const next = [...widgets]
  next.splice(at, 0, { id: `w-${crypto.randomUUID()}`, catalogId })
  return next
}

export const removeWidget = (widgets: BoardWidget[], id: string) => widgets.filter((widget) => widget.id !== id)

export const moveWidget = (widgets: BoardWidget[], id: string, step: -1 | 1) => {
  const from = widgets.findIndex((widget) => widget.id === id)
  const to = from + step
  if (from < 0 || to < 0 || to >= widgets.length) return widgets
  const next = [...widgets]
  ;[next[from], next[to]] = [next[to], next[from]]
  return next
}

export const dropWidget = (widgets: BoardWidget[], draggedId: string, targetId: string) => {
  const from = widgets.findIndex((widget) => widget.id === draggedId)
  const to = widgets.findIndex((widget) => widget.id === targetId)
  if (from < 0 || to < 0 || from === to) return widgets
  const next = [...widgets]
  const [dragged] = next.splice(from, 1)
  next.splice(to, 0, dragged)
  return next
}

export const resizeWidget = (widgets: BoardWidget[], id: string, allowed: SizeName[]) =>
  widgets.map((widget) => {
    if (widget.id !== id) return widget
    const next = allowed[(allowed.indexOf(widget.size ?? allowed[0]) + 1) % allowed.length]
    return { ...widget, size: next }
  })

export const arrangeWidgets = (widgets: BoardWidget[]) =>
  arrange(widgets, (widget) => widgetShape(catalog.find((entry) => entry.id === widget.catalogId)?.widget ?? '', widget.size))

export type CanvasOp =
  | { type: 'add'; catalogId: string }
  | { type: 'remove'; widgetId: string }
  | { type: 'resize'; widgetId: string; size: SizeName }
  | { type: 'replaceAll'; catalogIds: string[] }

const known = (catalogId: string) => catalog.some((entry) => entry.id === catalogId)

const applyOp = (widgets: BoardWidget[], op: CanvasOp): BoardWidget[] => {
  if (op.type === 'add') {
    const ok = known(op.catalogId) && widgets.length < MAX_WIDGETS && !widgets.some((widget) => widget.catalogId === op.catalogId)
    return ok ? addWidget(widgets, op.catalogId) : widgets
  }
  if (op.type === 'remove') return removeWidget(widgets, op.widgetId)
  if (op.type === 'replaceAll') return op.catalogIds.reduce((all, catalogId) => applyOp(all, { type: 'add', catalogId }), [])
  const entry = catalog.find((candidate) => candidate.id === widgets.find((widget) => widget.id === op.widgetId)?.catalogId)
  if (!entry || !allowedSizes(entry.widget).includes(op.size)) return widgets
  return widgets.map((widget) => (widget.id === op.widgetId ? { ...widget, size: op.size } : widget))
}

export const applyOps = (widgets: BoardWidget[], ops: CanvasOp[]) => ops.reduce(applyOp, widgets)
