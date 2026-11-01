import { useCallback, useEffect, useState } from 'react'
import { CompanyNotAllowed } from './catalogClient'
import type { CatalogClient, CatalogEntry } from './catalogClient'

export type CatalogState = { status: 'idle' } | { status: 'loading' } | { status: 'failed' } | { status: 'denied' } | { status: 'ready'; entries: CatalogEntry[] }

export function useCatalog(client: CatalogClient, enabled: boolean, company: string | null) {
  const [state, setState] = useState<CatalogState>({ status: 'idle' })

  const load = useCallback(() => {
    setState({ status: 'loading' })
    client.list(company).then(
      (entries) => setState({ status: 'ready', entries }),
      (error) => setState({ status: error instanceof CompanyNotAllowed ? 'denied' : 'failed' }),
    )
  }, [client, company])

  useEffect(() => {
    if (enabled) load()
    else setState({ status: 'idle' })
  }, [enabled, load])

  return { state, retry: load }
}
