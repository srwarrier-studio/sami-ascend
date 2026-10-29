import { useEffect, useState } from 'react'
import { Alert, Skeleton, registry } from '@sami/ui'
import type { SalesData } from '../data/salesData'
import type { CatalogEntry } from './catalog'

type State = { status: 'loading' } | { status: 'failed'; message: string } | { status: 'ready'; props: object }

export function CatalogWidget({ entry, data }: { entry: CatalogEntry; data: SalesData }) {
  const [state, setState] = useState<State>({ status: 'loading' })

  useEffect(() => {
    let current = true
    entry
      .load(data)
      .then((props) => current && setState({ status: 'ready', props }))
      .catch((error: unknown) => current && setState({ status: 'failed', message: error instanceof Error ? error.message : 'Could not load' }))
    return () => {
      current = false
    }
  }, [entry, data])

  if (state.status === 'loading') return <Skeleton height={160} radius="lg" aria-label={`Loading ${entry.title}`} />
  if (state.status === 'failed') return <Alert color="red" title={entry.title}>{state.message}</Alert>
  return registry.render(entry.widget, state.props)
}
