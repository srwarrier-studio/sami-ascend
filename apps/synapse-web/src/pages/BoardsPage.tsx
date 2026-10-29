import { useState } from 'react'
import { useRouteContext } from '@tanstack/react-router'
import { Button, Group, Modal, PageBar, PageHeader, PencilSimpleIcon, PlusIcon, SparkleIcon, Text, TrashIcon, useColorScheme } from '@sami/ui'
import { AiDrawer } from '../boards/AiDrawer'
import { BoardGrid } from '../boards/BoardGrid'
import { CatalogPicker } from '../boards/CatalogPicker'
import { addWidget } from '../boards/layout'
import { useBoards } from '../boards/useBoards'

export function BoardsPage() {
  const { boardStore, salesData, ui, setUi } = useRouteContext({ from: '/' })
  const { colorScheme, setColorScheme } = useColorScheme()
  const { boards, active, select, add, rename, remove, setWidgets } = useBoards(boardStore)
  const [editing, setEditing] = useState(false)
  const [picking, setPicking] = useState(false)
  const [asking, setAsking] = useState(false)
  const [deleting, setDeleting] = useState(false)

  if (!boards || !active) return null

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
            {editing && (
              <>
                <Button variant="light" leftSection={<SparkleIcon size={16} weight="fill" />} onClick={() => setAsking(true)}>
                  AI Mode
                </Button>
                <Button leftSection={<PlusIcon size={16} />} onClick={() => setPicking(true)}>
                  Add widget
                </Button>
              </>
            )}
          </Group>
        }
      />
      {active.widgets.length === 0 && (
        <Text c="dimmed" p="md">
          This board is empty. Press Edit, then Add widget.
        </Text>
      )}
      <BoardGrid widgets={active.widgets} data={salesData} editing={editing} onChange={setWidgets} />
      <PageBar
        tabs={boards}
        activeId={active.id}
        config={{ ...ui, scheme: colorScheme === 'dark' ? 'dark' : 'light' }}
        onSelect={select}
        onAdd={add}
        onConfigChange={(config) => {
          setUi({ palette: config.palette, motion: config.motion })
          setColorScheme(config.scheme)
        }}
      />
      <Modal opened={picking} onClose={() => setPicking(false)} title="Add widget" size="lg">
        <CatalogPicker
          onPick={(catalogId) => {
            setWidgets(addWidget(active.widgets, catalogId))
            setPicking(false)
          }}
        />
      </Modal>
      <AiDrawer
        opened={asking}
        onClose={() => setAsking(false)}
        onAdd={(catalogIds) => setWidgets(catalogIds.reduce(addWidget, active.widgets))}
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
