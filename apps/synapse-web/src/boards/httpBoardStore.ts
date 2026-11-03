import { SYNAPSE_URL } from '../config'
import type { Board, BoardStore, BoardWidget, SharedBoard } from './boardStore'

type WireBoard = { id: string; name: string; isPublic: boolean; owner: string; widgets: { id: string; catalogId: string; size: string | null }[] }

const widgetsOf = (board: WireBoard): BoardWidget[] =>
  board.widgets.map((widget) => ({ id: widget.id, catalogId: widget.catalogId, ...(widget.size ? { size: widget.size as BoardWidget['size'] } : {}) }))

const boardOf = (board: WireBoard): Board => ({ id: board.id, name: board.name, isPublic: board.isPublic, widgets: widgetsOf(board) })

const call = async (method: string, path: string, body?: object) => {
  const response = await fetch(`${SYNAPSE_URL}/v1/synapse/boards${path}`, {
    method,
    credentials: 'include',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (response.status === 204) return null
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.code ?? `board request failed: ${response.status}`)
  return data
}

export class HttpBoardStore implements BoardStore {
  async list() {
    return ((await call('GET', '')) as WireBoard[]).map(boardOf)
  }

  async create(name: string) {
    return boardOf(await call('POST', '', { name }))
  }

  async rename(id: string, name: string) {
    await call('PATCH', `/${id}`, { name })
  }

  async remove(id: string) {
    await call('DELETE', `/${id}`)
  }

  async saveWidgets(id: string, widgets: BoardWidget[]) {
    await call('PUT', `/${id}/widgets`, { widgets: widgets.map((widget) => ({ id: widget.id, catalogId: widget.catalogId, size: widget.size ?? null })) })
  }

  async setPublic(id: string, isPublic: boolean) {
    await call('PATCH', `/${id}`, { isPublic })
  }

  async listShared(): Promise<SharedBoard[]> {
    return ((await call('GET', '/shared')) as WireBoard[]).map((board) => ({ id: board.id, name: board.name, owner: board.owner, widgets: widgetsOf(board) }))
  }
}
