import { useCallback, useEffect, useState } from 'react'
import type { Board, BoardStore, BoardWidget } from './boardStore'

export function useBoards(store: BoardStore) {
  const [boards, setBoards] = useState<Board[] | null>(null)
  const [activeId, setActiveId] = useState('')

  useEffect(() => {
    store.list().then((loaded) => {
      setBoards(loaded)
      setActiveId((current) => current || loaded[0]?.id || '')
    })
  }, [store])

  const active = boards?.find((board) => board.id === activeId) ?? boards?.[0]

  const add = useCallback(async () => {
    const created = await store.create(`Board ${(boards?.length ?? 0) + 1}`)
    setBoards((current) => [...(current ?? []), created])
    setActiveId(created.id)
  }, [store, boards])

  const rename = useCallback(
    async (name: string) => {
      if (!active) return
      await store.rename(active.id, name)
      setBoards((current) => current?.map((board) => (board.id === active.id ? { ...board, name } : board)) ?? null)
    },
    [store, active],
  )

  const remove = useCallback(async () => {
    if (!active || !boards || boards.length < 2) return
    await store.remove(active.id)
    const rest = boards.filter((board) => board.id !== active.id)
    setBoards(rest)
    setActiveId(rest[0].id)
  }, [store, active, boards])

  const setWidgets = useCallback(
    async (widgets: BoardWidget[]) => {
      if (!active) return
      setBoards((current) => current?.map((board) => (board.id === active.id ? { ...board, widgets } : board)) ?? null)
      await store.saveWidgets(active.id, widgets)
    },
    [store, active],
  )

  return { boards, active, select: setActiveId, add, rename, remove, setWidgets }
}
