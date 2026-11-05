import { masterDataClient as client } from '../src/api/masterData'

const URL = 'http://localhost:8002/v1/workspace/master-data'

const respond = (status: number, body: unknown) =>
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status })))

afterEach(() => vi.unstubAllGlobals())

describe('master data client', () => {
  it('reads the plants with the cookie', async () => {
    respond(200, { plants: [{ plant: '1000', name: 'Plant', company_code: 'INA1' }] })
    expect(await client.plants()).toEqual([{ plant: '1000', name: 'Plant', company_code: 'INA1' }])
    const [url, init] = vi.mocked(fetch).mock.calls[0]
    expect(url).toBe(`${URL}/plants`)
    expect(init).toMatchObject({ credentials: 'include' })
  })

  it('searches materials of a plant', async () => {
    respond(200, { materials: [{ material: 'M1' }], total: 1 })
    expect(await client.materials('bolt', '1000')).toEqual([{ material: 'M1' }])
    expect(vi.mocked(fetch).mock.calls[0][0]).toBe(`${URL}/materials?q=bolt&plant=1000&top=20`)
  })

  it('leaves the empty search and the missing plant out of the address', async () => {
    respond(200, { materials: [], total: 0 })
    await client.materials('')
    expect(vi.mocked(fetch).mock.calls[0][0]).toBe(`${URL}/materials?top=20`)
  })

  it('encodes what the user typed', async () => {
    respond(200, { customers: [], total: 0 })
    await client.customers("o'neil & co")
    expect(vi.mocked(fetch).mock.calls[0][0]).toBe(`${URL}/customers?q=o%27neil+%26+co&top=20`)
  })

  it('reads customers and suppliers', async () => {
    respond(200, { customers: [{ number: 'C1', name: 'Acme', company_codes: ['INA1'] }], total: 1 })
    expect(await client.customers('')).toEqual([{ number: 'C1', name: 'Acme', company_codes: ['INA1'] }])
    respond(200, { suppliers: [{ number: 'S1', name: 'Supply', company_codes: ['INA1'] }], total: 1 })
    expect(await client.suppliers('')).toEqual([{ number: 'S1', name: 'Supply', company_codes: ['INA1'] }])
  })

  it.each([401, 403, 422, 503])('throws on %i', async (status) => {
    respond(status, {})
    await expect(client.plants()).rejects.toThrow(`plants failed: ${status}`)
  })
})
