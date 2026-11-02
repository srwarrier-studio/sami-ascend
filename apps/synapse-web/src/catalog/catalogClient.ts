import { SYNAPSE_URL } from '../config'

export type CatalogEntry = { id: string; title: string; description: string; category: string; widget: string }

export type Summary = { asOf: string; currency: string; sentences: string[] }

export type CatalogClient = {
  list: (company: string | null) => Promise<CatalogEntry[]>
  data: (id: string, company: string | null, currency: string, top?: number) => Promise<object>
  summary: (company: string | null, currency: string) => Promise<Summary>
}

export class CompanyNotAllowed extends Error {
  constructor() {
    super('You do not have access to this company')
  }
}

const get = async (path: string, company: string | null, currency?: string, top?: number) => {
  const params = new URLSearchParams()
  if (company) params.set('company', company)
  if (currency) params.set('currency', currency)
  if (top) params.set('top', String(top))
  const query = params.size > 0 ? `?${params}` : ''
  const response = await fetch(`${SYNAPSE_URL}/v1/synapse${path}${query}`, { credentials: 'include' })
  if (response.ok) return response.json()
  const body = await response.json().catch(() => ({}))
  if (response.status === 403 && body.code === 'COMPANY_NOT_ALLOWED') throw new CompanyNotAllowed()
  throw new Error(body.message ?? body.code ?? `catalog request failed: ${response.status}`)
}

export class HttpCatalogClient implements CatalogClient {
  async list(company: string | null) {
    return (await get('/catalog', company)).entries as CatalogEntry[]
  }

  async data(id: string, company: string | null, currency: string, top?: number) {
    return (await get(`/catalog/${encodeURIComponent(id)}/data`, company, currency, top)) as object
  }

  async summary(company: string | null, currency: string) {
    return (await get('/summary', company, currency)) as Summary
  }
}
