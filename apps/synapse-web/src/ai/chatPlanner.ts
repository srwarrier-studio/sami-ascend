import { allowedSizes } from '@sami/ui'
import { catalog, matchCatalog } from '../catalog/catalog'
import type { CanvasOp } from '../boards/layout'
import type { BoardWidget } from '../boards/boardStore'

export type ChatPlan = { reply: string; ops: CanvasOp[]; boardName?: string }

export type ChatPlanner = {
  plan: (message: string, canvas: BoardWidget[]) => Promise<ChatPlan>
}

const categories = [...new Set(catalog.map((entry) => entry.category))]
const has = (text: string, ...words: string[]) => words.some((word) => text.includes(word))
const titleOf = (widget: BoardWidget) => catalog.find((entry) => entry.id === widget.catalogId)?.title ?? widget.catalogId

export class MockChatPlanner implements ChatPlanner {
  async plan(message: string, canvas: BoardWidget[]): Promise<ChatPlan> {
    const text = message.toLowerCase()
    if (has(text, 'start over', 'clear')) return { reply: 'Cleared the canvas.', ops: [{ type: 'replaceAll', catalogIds: [] }] }

    if (has(text, 'remove', 'delete')) {
      const ids = matchCatalog(text.replace(/remove|delete/g, '')).map((entry) => entry.id)
      const found = canvas.filter((widget) => ids.includes(widget.catalogId))
      if (found.length > 0) return { reply: `Removed ${found.map(titleOf).join(', ')}.`, ops: found.map((widget) => ({ type: 'remove', widgetId: widget.id })) }
    }

    if (has(text, 'bigger', 'larger', 'smaller')) {
      const last = canvas[canvas.length - 1]
      const entry = catalog.find((candidate) => candidate.id === last?.catalogId)
      if (last && entry) {
        const sizes = allowedSizes(entry.widget)
        const at = sizes.indexOf(last.size ?? sizes[0]) + (has(text, 'smaller') ? -1 : 1)
        const size = sizes[Math.min(Math.max(at, 0), sizes.length - 1)]
        return { reply: `Made ${titleOf(last)} ${has(text, 'smaller') ? 'smaller' : 'bigger'}.`, ops: [{ type: 'resize', widgetId: last.id, size }] }
      }
    }

    const category = categories.find((name) => text.includes(name.toLowerCase()))
    if (category && has(text, 'build', 'board', 'review', 'overview')) {
      const ids = catalog.filter((entry) => entry.category === category).map((entry) => entry.id)
      return { reply: `Here is a ${category} board.`, ops: [{ type: 'replaceAll', catalogIds: ids }], boardName: `${category} review` }
    }

    const added = matchCatalog(text).filter((entry) => !canvas.some((widget) => widget.catalogId === entry.id))
    if (added.length > 0) return { reply: `Added ${added.map((entry) => entry.title).join(', ')}.`, ops: added.map((entry) => ({ type: 'add', catalogId: entry.id })) }

    return { reply: `I could not match that. Try "build a ${categories[0]} board" or "show top customers".`, ops: [] }
  }
}
