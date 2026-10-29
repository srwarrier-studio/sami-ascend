import { useState } from 'react'
import { useNavigate, useRouteContext, useSearch } from '@tanstack/react-router'
import { Button, EmptyBoard, Group, Modal, PageBar, PageHeader, PencilSimpleIcon, PlusIcon, SparkleIcon, Text, TrashIcon, WidgetLibrary, notifications, useColorScheme } from '@sami/ui'
import { BoardGrid } from '../boards/BoardGrid'
import { catalog } from '../catalog/catalog'
import { MAX_WIDGETS, arrangeWidgets, insertWidget, removeWidget } from '../boards/layout'
import { useBoards } from '../boards/useBoards'

export function BoardsPage() {
  const navigate = useNavigate()
  const search = useSearch({ from: '/' })
  const { boardStore, salesData, ui, setUi } = useRouteContext({ from: '/' })
  const { colorScheme, setColorScheme } = useColorScheme()
  const { boards, active, select, add, rename, remove, setWidgets } = useBoards(boardStore, search.board)
  const [editing, setEditing] = useState(false)
  const [picking, setPicking] = useState(false)
  const [deleting, setDeleting] = useState(false)

  if (!boards || !active) return null

  const insert = (catalogId: string, beforeId: string | null) => {
    if (active.widgets.some((widget) => widget.catalogId === catalogId)) return
    if (active.widgets.length >= MAX_WIDGETS) {
      notifications.show({ message: `Only ${MAX_WIDGETS} widgets allowed on a board` })
      return
    }
    setWidgets(insertWidget(active.widgets, catalogId, beforeId))
  }

  return (
    <>
      <PageHeader
        title={active.name}
        breadcrumb={['Boards']}
        editing={editing}
        onTitleChange={rename}
        actions={
          <Group>
            {editing && (
              <Button variant="subtle" color="red" leftSection={<TrashIcon size={16} />} disabled={boards.length < 2} onClick={() => setDeleting(true)}>
                Delete board
              </Button>
            )}
            <Button variant={editing ? 'filled' : 'default'} leftSection={<PencilSimpleIcon size={16} />} onClick={() => setEditing(!editing)}>
              {editing ? 'Done' : 'Edit'}
            </Button>
            <Button variant="light" leftSection={<SparkleIcon size={16} weight="fill" />} onClick={() => navigate({ to: '/ai' })}>
              AI Mode
            </Button>
            <Button
              leftSection={<PlusIcon size={16} />}
              onClick={() => {
                setEditing(true)
                setPicking(true)
              }}
            >
              Add widget
            </Button>
          </Group>
        }
      />
      <BoardGrid widgets={active.widgets} data={salesData} editing={editing} onChange={setWidgets}
        empty={active.widgets.length === 0 && <EmptyBoard editing={editing} onEdit={() => setEditing(true)} onAdd={() => setPicking(true)} />}
      />
      <PageBar
        tabs={boards}
        activeId={active.id}
        config={{ ...ui, scheme: colorScheme === 'dark' ? 'dark' : 'light' }}
        onSelect={select}
        onAdd={add}
        onArrange={editing ? () => setWidgets(arrangeWidgets(active.widgets)) : undefined}
        onConfigChange={(config) => {
          setUi({ palette: config.palette, motion: config.motion })
          setColorScheme(config.scheme)
        }}
      />
      <WidgetLibrary
        opened={picking}
        onClose={() => setPicking(false)}
        items={catalog}
        limit={{ used: active.widgets.length, max: MAX_WIDGETS }}
        counts={active.widgets.reduce<Record<string, number>>((all, widget) => ({ ...all, [widget.catalogId]: (all[widget.catalogId] ?? 0) + 1 }), {})}
        onPick={(catalogId) => insert(catalogId, null)}
        onRemove={(catalogId) => setWidgets(removeWidget(active.widgets, active.widgets.find((widget) => widget.catalogId === catalogId)?.id ?? ''))}
      />
      <Modal opened={deleting} onClose={() => setDeleting(false)} title="Delete board">
        <Text>Delete {active.name} and its widgets?</Text>
        <Group justify="flex-end" mt="md">
          <Button variant="default" onClick={() => setDeleting(false)}>
            Cancel
          </Button>
          <Button
            color="red"
            onClick={() => {
              remove()
              setDeleting(false)
              setEditing(false)
            }}
          >
            Delete
          </Button>
        </Group>
      </Modal>
    </>
  )
}
