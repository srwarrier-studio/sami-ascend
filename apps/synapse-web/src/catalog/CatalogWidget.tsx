import { useEffect, useState } from 'react'
import { Alert, Skeleton, registry } from '@sami/ui'
import type { CatalogClient, CatalogEntry } from './catalogClient'

type State = { status: 'loading' } | { status: 'failed'; message: string } | { status: 'ready'; props: Record<string, unknown> }

export const REFRESH_MS = 300000
export const CURRENCY = 'INR'

type CatalogWidgetProps = { entry: CatalogEntry; client: CatalogClient; company: string | null; refreshMs?: number; onLoaded?: (at: Date) => void }

export function CatalogWidget({ entry, client, company, refreshMs = REFRESH_MS, onLoaded }: CatalogWidgetProps) {
  const [state, setState] = useState<State>({ status: 'loading' })

  useEffect(() => {
    let current = true
    const load = () =>
      client
        .data(entry.id, company, CURRENCY)
        .then((props) => {
          if (!current) return
          setState({ status: 'ready', props: props as Record<string, unknown> })
          onLoaded?.(new Date())
        })
        .catch((error: unknown) => current && setState({ status: 'failed', message: error instanceof Error ? error.message : 'Could not load' }))
    load()
    const timer = setInterval(load, refreshMs)
    return () => {
      current = false
      clearInterval(timer)
    }
  }, [entry, client, company, refreshMs, onLoaded])

  if (state.status === 'loading') return <Skeleton height="100%" radius="lg" aria-label={`Loading ${entry.title}`} />
  if (state.status === 'failed') return <Alert color="red" title={entry.title}>{state.message}</Alert>
  const named = typeof state.props.currency === 'string' && /^[A-Z]{3}$/.test(state.props.currency) ? state.props.currency : null
  const props = named && state.props.valueFormat === 'currency' ? { ...state.props, valueFormat: `currency:${named}` } : state.props
  return registry.render(entry.widget, props)
}
