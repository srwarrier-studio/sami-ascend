import { SYNAPSE_URL } from '../config'

export type CatalogEntry = { id: string; title: string; description: string; category: string; widget: string }

export type CatalogClient = {
  list: () => Promise<CatalogEntry[]>
  data: (id: string) => Promise<object>
}

const get = async (path: string) => {
  const response = await fetch(`${SYNAPSE_URL}/v1/synapse${path}`, { credentials: 'include' })
  if (response.ok) return response.json()
  const body = await response.json().catch(() => ({}))
  throw new Error(body.message ?? body.code ?? `catalog request failed: ${response.status}`)
}

export class HttpCatalogClient implements CatalogClient {
  async list() {
    return (await get('/catalog')).entries as CatalogEntry[]
  }

  async data(id: string) {
    return (await get(`/catalog/${encodeURIComponent(id)}/data`)) as object
  }
}
