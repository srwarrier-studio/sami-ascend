import { useCallback, useEffect, useState } from 'react'
import type { CatalogClient, CatalogEntry } from './catalogClient'

export type CatalogState = { status: 'idle' } | { status: 'loading' } | { status: 'failed' } | { status: 'ready'; entries: CatalogEntry[] }

export function useCatalog(client: CatalogClient, enabled: boolean) {
  const [state, setState] = useState<CatalogState>({ status: 'idle' })

  const load = useCallback(() => {
    setState({ status: 'loading' })
    client.list().then(
      (entries) => setState({ status: 'ready', entries }),
      () => setState({ status: 'failed' }),
    )
  }, [client])

  useEffect(() => {
    if (enabled) load()
    else setState({ status: 'idle' })
  }, [enabled, load])

  return { state, retry: load }
}
