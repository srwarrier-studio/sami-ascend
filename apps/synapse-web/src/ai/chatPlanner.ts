import { catalog, matchCatalog } from '../catalog/catalog'

export type ChatBoard = { name: string; catalogIds: string[] }
export type ChatReply = { reply: string; catalogIds: string[]; board?: ChatBoard }

export type ChatPlanner = {
  plan: (message: string) => Promise<ChatReply>
}

export const BUILDER = '@builder'
const MAX_INLINE = 4
const categories = [...new Set(catalog.map((entry) => entry.category))]

export class MockChatPlanner implements ChatPlanner {
  async plan(message: string): Promise<ChatReply> {
    const text = message.trim()
    if (text.toLowerCase().startsWith(BUILDER)) return this.build(text.slice(BUILDER.length).toLowerCase())

    const found = matchCatalog(text).slice(0, MAX_INLINE)
    if (found.length === 0) return { reply: `I could not match that. Try "show top customers", or "${BUILDER} build a sales board" for a whole board.`, catalogIds: [] }
    return { reply: `Here is ${found.map((entry) => entry.title).join(', ')}.`, catalogIds: found.map((entry) => entry.id) }
  }

  private build(request: string): ChatReply {
    const category = categories.find((name) => request.includes(name.toLowerCase()))
    const entries = category ? catalog.filter((entry) => entry.category === category) : matchCatalog(request)
    if (entries.length === 0) return { reply: `Tell me what to build, for example "${BUILDER} build an inventory board".`, catalogIds: [] }
    const board = { name: category ? `${category} review` : 'My board', catalogIds: entries.map((entry) => entry.id) }
    return { reply: `I built "${board.name}" with ${board.catalogIds.length} widgets.`, catalogIds: [], board }
  }
}
