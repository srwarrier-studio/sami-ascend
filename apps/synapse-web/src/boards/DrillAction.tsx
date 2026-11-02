import { useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Button, Modal } from '@sami/ui'
import { CatalogWidget } from '../catalog/CatalogWidget'
import type { CatalogClient, CatalogEntry } from '../catalog/catalogClient'
import classes from './Board.module.css'

export const WHY_QUESTION = 'Why did sales change last month?'
export const SEE_ALL_ROWS = 20

const WHY = new Set(['sales-today', 'sales-month', 'sales-year', 'day-sales', 'month-on-month'])
const SEE_ALL = new Set(['top-customers', 'top-materials', 'high-value-sales'])

type DrillActionProps = { entry: CatalogEntry; client: CatalogClient; company: string | null }

export function DrillAction({ entry, client, company }: DrillActionProps) {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  if (WHY.has(entry.id))
    return (
      <Button className={classes.drill} size="compact-xs" variant="subtle" aria-label={`Why did ${entry.title} change?`} onClick={() => navigate({ to: '/ai', search: { ask: WHY_QUESTION } })}>
        Why?
      </Button>
    )
  if (!SEE_ALL.has(entry.id)) return null
  return (
    <>
      <Button className={classes.drill} size="compact-xs" variant="subtle" aria-label={`See all ${entry.title}`} onClick={() => setOpen(true)}>
        See all
      </Button>
      <Modal opened={open} onClose={() => setOpen(false)} title={entry.title} size="lg" closeButtonProps={{ 'aria-label': 'Close' }}>
        <CatalogWidget entry={entry} client={client} company={company} top={SEE_ALL_ROWS} />
      </Modal>
    </>
  )
}
