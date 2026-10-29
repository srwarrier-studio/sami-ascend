import { useRef, useState } from 'react'
import type { DragEvent, ReactNode } from 'react'
import { LIBRARY_DRAG, ActionIcon, ArrowLeftIcon, ArrowRightIcon, ArrowsOutSimpleIcon, TrashIcon, WidgetCell, WidgetGrid, allowedSizes } from '@sami/ui'
import { CatalogWidget } from '../catalog/CatalogWidget'
import { catalog } from '../catalog/catalog'
import type { SalesData } from '../data/salesData'
import type { BoardWidget } from './boardStore'
import { dropWidget, moveWidget, removeWidget, resizeWidget } from './layout'
import classes from './Board.module.css'

type BoardGridProps = {
  widgets: BoardWidget[]
  data: SalesData
  editing: boolean
  onChange: (widgets: BoardWidget[]) => void
  onInsert: (catalogId: string, beforeId: string | null) => void
  empty?: ReactNode
}

const isLibraryDrag = (event: DragEvent<HTMLElement>) => event.dataTransfer.types.includes(LIBRARY_DRAG)

export function BoardGrid({ widgets, data, editing, onChange, onInsert, empty }: BoardGridProps) {
  const [dragging, setDragging] = useState<string | null>(null)
  const [preview, setPreview] = useState<BoardWidget[] | null>(null)
  const shown = preview ?? widgets
  const lastMove = useRef(0)
  const [overId, setOverId] = useState<string | null>(null)

  return (
    <div
      className={classes.board}
      onDragOver={(event) => isLibraryDrag(event) && event.preventDefault()}
      onDragLeave={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setOverId(null)
      }}
      onDrop={(event) => {
        if (!isLibraryDrag(event)) return
        event.preventDefault()
        onInsert(event.dataTransfer.getData(LIBRARY_DRAG), null)
        setOverId(null)
      }}
    >
      {empty}
      <WidgetGrid>
      {shown.map((widget) => {
        const entry = catalog.find((candidate) => candidate.id === widget.catalogId)
        if (!entry) return null
        return (
          <WidgetCell
            key={widget.id}
            widget={entry.widget}
            size={widget.size}
            editing={editing}
            dragging={dragging === widget.id}
            over={overId === widget.id}
            draggable={editing}
            onDragStart={() => setTimeout(() => setDragging(widget.id))}
            onDragEnd={() => {
              if (preview) onChange(preview)
              setDragging(null)
              setPreview(null)
            }}
            onDragEnter={() => {
              if (!editing || !dragging || dragging === widget.id || Date.now() - lastMove.current < 300) return
              lastMove.current = Date.now()
              setPreview(dropWidget(shown, dragging, widget.id))
            }}
            onDragOver={(event) => {
              if (isLibraryDrag(event)) setOverId(widget.id)
              if (editing || isLibraryDrag(event)) event.preventDefault()
            }}
            onDrop={(event) => {
              if (!isLibraryDrag(event)) return
              event.preventDefault()
              event.stopPropagation()
              onInsert(event.dataTransfer.getData(LIBRARY_DRAG), widget.id)
              setOverId(null)
            }}
          >
            {editing && (
              <div className={classes.controls}>
                <ActionIcon variant="light" size="sm" aria-label={`Move ${entry.title} earlier`} onClick={() => onChange(moveWidget(widgets, widget.id, -1))}>
                  <ArrowLeftIcon size={14} />
                </ActionIcon>
                <ActionIcon variant="light" size="sm" aria-label={`Move ${entry.title} later`} onClick={() => onChange(moveWidget(widgets, widget.id, 1))}>
                  <ArrowRightIcon size={14} />
                </ActionIcon>
                {allowedSizes(entry.widget).length > 1 && (
                  <ActionIcon variant="light" size="sm" aria-label={`Resize ${entry.title}`} onClick={() => onChange(resizeWidget(widgets, widget.id, allowedSizes(entry.widget)))}>
                    <ArrowsOutSimpleIcon size={14} />
                  </ActionIcon>
                )}
                <ActionIcon variant="light" color="red" size="sm" aria-label={`Remove ${entry.title}`} onClick={() => onChange(removeWidget(widgets, widget.id))}>
                  <TrashIcon size={14} />
                </ActionIcon>
              </div>
            )}
            <CatalogWidget entry={entry} data={data} />
          </WidgetCell>
        )
      })}
      </WidgetGrid>
    </div>
  )
}
