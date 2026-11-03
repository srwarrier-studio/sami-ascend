import { useRef, useState } from 'react'
import { flushSync } from 'react-dom'
import { useNavigate, useRouteContext, useSearch } from '@tanstack/react-router'
import { Alert, Button, EmptyBoard, Group, Modal, PageBar, PageHeader, FilePdfIcon, PencilSimpleIcon, PlusIcon, SparkleIcon, Text, TrashIcon, WidgetLibrary, clockTime, notifications, useColorScheme } from '@sami/ui'
import { BoardGrid } from '../boards/BoardGrid'
import { BoardsSkeleton } from '../boards/BoardsSkeleton'
import { SummaryStrip } from '../boards/SummaryStrip'
import { ExportFrame } from '../export/ExportFrame'
import { SaveBoardModal } from '../boards/SaveBoardModal'
import { listPresets } from '../boards/presets'
import { MAX_WIDGETS, arrangeWidgets, buildWidgets, insertWidget, removeWidget } from '../boards/layout'
import { useBoards } from '../boards/useBoards'

export function BoardsPage() {
  const navigate = useNavigate()
  const search = useSearch({ from: '/' })
  const { boardStore, catalog, catalogClient, boardExporter, session, company, ui, setUi } = useRouteContext({ from: '/' })
  const { colorScheme, setColorScheme } = useColorScheme()
  const { boards, active, select, reload, add, rename, remove, setWidgets } = useBoards(boardStore, search.board)
  const [editing, setEditing] = useState(false)
  const [picking, setPicking] = useState(false)
  const [presetId, setPresetId] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [generatedAt, setGeneratedAt] = useState(() => new Date())
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null)
  const frame = useRef<HTMLDivElement>(null)

  if (!boards) return <BoardsSkeleton />
  if (!active) return null

  const presets = listPresets(catalog)
  const chosenPreset = presets.find((preset) => preset.id === presetId)

  const insert = (catalogId: string, beforeId: string | null) => {
    if (active.widgets.some((widget) => widget.catalogId === catalogId)) return
    if (active.widgets.length >= MAX_WIDGETS) {
      notifications.show({ message: `Only ${MAX_WIDGETS} widgets allowed on a board` })
      return
    }
    setWidgets(insertWidget(active.widgets, catalogId, beforeId))
  }

  const exportPdf = async () => {
    const sheet = frame.current
    if (!sheet || exporting) return
    if (sheet.querySelector('[aria-label^="Loading"]')) {
      notifications.show({ message: 'Widgets are still loading' })
      return
    }
    flushSync(() => {
      setGeneratedAt(new Date())
      setExporting(true)
    })
    try {
      const day = new Date().toLocaleDateString('en-CA')
      await boardExporter.export(sheet, `${active.name.replace(/[\\/:*?"<>|]/g, '-')}-${day}.pdf`)
    } finally {
      setExporting(false)
    }
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
            {updatedAt && (
              <Text size="sm" c="dimmed">
                {`Updated ${clockTime(updatedAt.toISOString())}`}
              </Text>
            )}
            {!editing && (
              <Button variant="default" leftSection={<FilePdfIcon size={16} />} loading={exporting} onClick={exportPdf}>
                Export PDF
              </Button>
            )}
            {editing && (
              <Button variant="subtle" color="red" leftSection={<TrashIcon size={16} />} disabled={boards.length < 2} onClick={() => setDeleting(true)}>
                Delete board
              </Button>
            )}
            <Button variant="light" leftSection={<SparkleIcon size={16} weight="fill" />} onClick={() => navigate({ to: '/ai' })}>
              AI Mode
            </Button>
            <Button
              variant="default"
              leftSection={<PlusIcon size={16} />}
              onClick={() => {
                setEditing(true)
                setPicking(true)
              }}
            >
              Add widget
            </Button>
            <Button leftSection={<PencilSimpleIcon size={16} />} onClick={() => setEditing(!editing)}>
              {editing ? 'Done' : 'Edit'}
            </Button>
          </Group>
        }
      />
      {editing && (
        <Alert color="blue" mx="md" mb="xs" py="xs">
          Editing. Changes save automatically. Press Done when finished.
        </Alert>
      )}
      {!editing && <SummaryStrip client={catalogClient} company={company} widgets={active.widgets.map((widget) => widget.catalogId)} />}
      <ExportFrame exporting={exporting} company={company} userName={session.status === 'signedIn' ? session.user.name : ''} generatedAt={generatedAt} frameRef={frame}>
        <BoardGrid widgets={active.widgets} catalog={catalog} client={catalogClient} company={company} editing={editing} onChange={setWidgets} onLoaded={setUpdatedAt}
          empty={active.widgets.length === 0 && <EmptyBoard editing={editing} onEdit={() => setEditing(true)} onAdd={() => setPicking(true)} />}
        />
      </ExportFrame>
      <PageBar
        tabs={boards}
        activeId={active.id}
        config={{ ...ui, scheme: colorScheme === 'dark' ? 'dark' : 'light' }}
        onSelect={select}
        onAdd={add}
        onArrange={editing ? () => setWidgets(arrangeWidgets(active.widgets, catalog)) : undefined}
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
        presets={presets.map((preset) => ({ id: preset.id, name: preset.name, description: preset.description, count: preset.catalogIds.length }))}
        onUsePreset={setPresetId}
        onPick={(catalogId) => insert(catalogId, null)}
        onRemove={(catalogId) => setWidgets(removeWidget(active.widgets, active.widgets.find((widget) => widget.catalogId === catalogId)?.id ?? ''))}
      />
      <SaveBoardModal
        opened={!!chosenPreset}
        onClose={() => setPresetId(null)}
        store={boardStore}
        name={chosenPreset?.name ?? ''}
        widgets={chosenPreset ? buildWidgets(chosenPreset.catalogIds, catalog) : []}
        onSaved={async (boardId) => {
          setPresetId(null)
          setPicking(false)
          setEditing(false)
          await reload(boardId)
        }}
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
