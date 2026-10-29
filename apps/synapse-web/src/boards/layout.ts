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
