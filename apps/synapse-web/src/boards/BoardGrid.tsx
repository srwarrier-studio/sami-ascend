import { useState } from 'react'
import { ActionIcon, ArrowLeftIcon, ArrowRightIcon, TrashIcon } from '@sami/ui'
import { registry } from '@sami/ui'
import { CatalogWidget } from '../catalog/CatalogWidget'
import { catalog } from '../catalog/catalog'
import type { SalesData } from '../data/salesData'
import type { BoardWidget } from './boardStore'
import { dropWidget, moveWidget, removeWidget } from './layout'
import classes from './Board.module.css'

type BoardGridProps = {
  widgets: BoardWidget[]
  data: SalesData
  editing: boolean
  onChange: (widgets: BoardWidget[]) => void
}

const sizes = new Map(registry.describe().map((entry) => [entry.name, entry.size.defaultW]))

export function BoardGrid({ widgets, data, editing, onChange }: BoardGridProps) {
  const [dragging, setDragging] = useState<string | null>(null)

  return (
    <div className={classes.grid}>
      {widgets.map((widget) => {
        const entry = catalog.find((candidate) => candidate.id === widget.catalogId)
        if (!entry) return null
        return (
          <div
            key={widget.id}
            className={classes.cell}
            data-span={sizes.get(entry.widget) ?? 4}
            data-editing={editing || undefined}
            data-dragging={dragging === widget.id || undefined}
            draggable={editing}
            onDragStart={() => setDragging(widget.id)}
            onDragEnd={() => setDragging(null)}
            onDragOver={(event) => editing && event.preventDefault()}
            onDrop={() => {
              if (editing && dragging) onChange(dropWidget(widgets, dragging, widget.id))
              setDragging(null)
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
                <ActionIcon variant="light" color="red" size="sm" aria-label={`Remove ${entry.title}`} onClick={() => onChange(removeWidget(widgets, widget.id))}>
                  <TrashIcon size={14} />
                </ActionIcon>
              </div>
            )}
            <CatalogWidget entry={entry} data={data} />
          </div>
        )
      })}
    </div>
  )
}
