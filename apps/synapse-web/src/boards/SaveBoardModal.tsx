import { useEffect, useState } from 'react'
import { Button, Group, Modal, Radio, Stack, Text, TextInput } from '@sami/ui'
import type { Board, BoardStore, BoardWidget } from './boardStore'
import { MAX_BOARDS } from './useBoards'

type SaveBoardModalProps = {
  opened: boolean
  onClose: () => void
  store: BoardStore
  name: string
  widgets: BoardWidget[]
  onSaved: (boardId: string) => void
}

export function SaveBoardModal({ opened, onClose, store, name, widgets, onSaved }: SaveBoardModalProps) {
  const [boards, setBoards] = useState<Board[] | null>(null)
  const [title, setTitle] = useState(name)
  const [replaceId, setReplaceId] = useState('')

  useEffect(() => {
    if (!opened) return
    setTitle(name)
    setReplaceId('')
    store.list().then(setBoards)
  }, [opened, store, name])

  const full = (boards?.length ?? 0) >= MAX_BOARDS
  const target = boards?.find((board) => board.id === replaceId)

  const save = async () => {
    if (full && target) {
      await store.rename(target.id, title.trim() || target.name)
      await store.saveWidgets(target.id, widgets)
      onSaved(target.id)
      return
    }
    const created = await store.create(title.trim() || name)
    await store.saveWidgets(created.id, widgets)
    onSaved(created.id)
  }

  return (
    <Modal opened={opened} onClose={onClose} title="Save as board">
      {boards && (
        <Stack>
          <TextInput label="Board name" maxLength={30} value={title} onChange={(event) => setTitle(event.currentTarget.value)} />
          {full && (
            <Radio.Group label="You have 3 boards. Pick one to replace" value={replaceId} onChange={setReplaceId}>
              <Stack gap="xs" mt="xs">
                {boards.map((board) => (
                  <Radio key={board.id} value={board.id} label={board.name} />
                ))}
              </Stack>
            </Radio.Group>
          )}
          {full && target && <Text size="sm" c="dimmed">{target.name} and its widgets will be replaced.</Text>}
          <Group justify="flex-end">
            <Button variant="default" onClick={onClose}>
              Cancel
            </Button>
            <Button disabled={!title.trim() || (full && !target)} color={full ? 'red' : undefined} onClick={save}>
              {full ? `Replace ${target?.name ?? 'board'}` : 'Save'}
            </Button>
          </Group>
        </Stack>
      )}
    </Modal>
  )
}
