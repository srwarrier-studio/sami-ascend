import { HttpCatalogClient } from '../src/catalog/catalogClient'

const respond = (status: number, body: unknown = {}) => vi.fn(async () => new Response(JSON.stringify(body), { status }))

const stub = (fetchMock: ReturnType<typeof respond>) => {
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => vi.unstubAllGlobals())

const entry = { id: 'sales-today', title: 'Sales today', description: 'd', category: 'Sales', widget: 'KpiCard' }

describe('listing the catalog', () => {
  it('reads the entries from synapse-api with credentials', async () => {
    const fetchMock = stub(respond(200, { entries: [entry] }))
    expect(await new HttpCatalogClient().list()).toEqual([entry])
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('http://localhost:8004/v1/synapse/catalog')
    expect(init.credentials).toBe('include')
  })

  it('throws with the status when the call fails', async () => {
    stub(respond(403))
    await expect(new HttpCatalogClient().list()).rejects.toThrow('catalog request failed: 403')
  })
})

describe('reading a widget', () => {
  it('returns the widget props for the id', async () => {
    const fetchMock = stub(respond(200, { title: 'Sales today', value: 5 }))
    expect(await new HttpCatalogClient().data('sales-today')).toEqual({ title: 'Sales today', value: 5 })
    expect((fetchMock.mock.calls[0] as unknown as [string])[0]).toBe('http://localhost:8004/v1/synapse/catalog/sales-today/data')
  })

  it('throws the server code for an unknown id', async () => {
    stub(respond(404, { code: 'CATALOG_ENTRY_NOT_FOUND' }))
    await expect(new HttpCatalogClient().data('nope')).rejects.toThrow('CATALOG_ENTRY_NOT_FOUND')
  })
})
