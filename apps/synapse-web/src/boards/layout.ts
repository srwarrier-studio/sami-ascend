import type { SizeName } from '@sami/ui'
import type { BoardWidget } from './boardStore'

export const addWidget = (widgets: BoardWidget[], catalogId: string): BoardWidget[] => [
  ...widgets,
  { id: `w-${crypto.randomUUID()}`, catalogId },
]

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
