import { purchaseRequisitionClient as client } from '../src/api/purchaseRequisitions'
import type { NewRequisition } from '../src/api/purchaseRequisitions'

const URL = 'http://localhost:8002/v1/workspace/purchase-requisitions'
const requisition = { purchase_requisition: '10000000', items: [] }
const draft: NewRequisition = {
  description: 'Spares',
  items: [{ material: 'RM-1001', plant: '1000', quantity: '5', unit: 'KG', delivery_date: '2026-12-01' }],
}

const respond = (status: number, body: unknown) =>
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status })))

afterEach(() => vi.unstubAllGlobals())

describe('create', () => {
  it('posts json with the cookie and returns the requisition on 201', async () => {
    respond(201, requisition)
    expect(await client.create(draft)).toEqual({ ok: true, requisition })
    const [url, init] = vi.mocked(fetch).mock.calls[0]
    expect(url).toBe(URL)
    expect(init).toMatchObject({ method: 'POST', credentials: 'include', body: JSON.stringify(draft) })
  })

  it('returns the details of a 422', async () => {
    const details = [{ code: 'MATERIAL_UNKNOWN', target: 'items/0/material', message: 'No such material' }]
    respond(422, { code: 'VALIDATION_FAILED', details })
    expect(await client.create(draft)).toEqual({ ok: false, kind: 'validation', details })
  })

  it.each([
    [403, 'notAllowed'],
    [404, 'notFound'],
    [503, 'unavailable'],
    [500, 'failed'],
  ])('maps %i to %s', async (status, kind) => {
    respond(status, { code: 'X' })
    expect(await client.create(draft)).toEqual({ ok: false, kind })
  })

  it('treats another 422 as failed', async () => {
    respond(422, { code: 'INVALID_QUERY' })
    expect(await client.create(draft)).toEqual({ ok: false, kind: 'failed' })
  })

  it('is failed when the network is down', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('down')))
    expect(await client.create(draft)).toEqual({ ok: false, kind: 'failed' })
  })
})

describe('list', () => {
  it('asks for the page and returns it', async () => {
    respond(200, { requisitions: [requisition], total: 1 })
    expect(await client.list(20, 40)).toEqual({ requisitions: [requisition], total: 1 })
    expect(vi.mocked(fetch).mock.calls[0][0]).toBe(`${URL}?top=20&skip=40`)
  })

  it('throws when the call fails', async () => {
    respond(503, {})
    await expect(client.list(20, 0)).rejects.toThrow('list failed: 503')
  })
})

describe('get', () => {
  it('returns the requisition', async () => {
    respond(200, requisition)
    expect(await client.get('10000000')).toEqual(requisition)
    expect(vi.mocked(fetch).mock.calls[0][0]).toBe(`${URL}/10000000`)
  })

  it('returns null on 404', async () => {
    respond(404, {})
    expect(await client.get('10000099')).toBeNull()
  })

  it('throws on another failure', async () => {
    respond(503, {})
    await expect(client.get('10000000')).rejects.toThrow('get failed: 503')
  })
})

describe('release', () => {
  it('posts the code, with the item only when given', async () => {
    respond(200, requisition)
    await client.release('10000000', '01')
    expect(vi.mocked(fetch).mock.calls[0][1]).toMatchObject({ body: JSON.stringify({ release_code: '01' }) })
    expect(vi.mocked(fetch).mock.calls[0][0]).toBe(`${URL}/10000000/release`)
    respond(200, requisition)
    await client.release('10000000', '01', '10')
    expect(vi.mocked(fetch).mock.calls[0][1]).toMatchObject({ body: JSON.stringify({ release_code: '01', item: '10' }) })
  })

  it('returns the refusal details of a 422', async () => {
    const details = [{ code: 'RELEASE_REFUSED', target: 'release_code', message: 'Not the next code' }]
    respond(422, { code: 'VALIDATION_FAILED', details })
    expect(await client.release('10000000', '02')).toEqual({ ok: false, kind: 'validation', details })
  })

  it('maps 403 and 404', async () => {
    respond(403, {})
    expect(await client.release('1', '01')).toEqual({ ok: false, kind: 'notAllowed' })
    respond(404, {})
    expect(await client.release('1', '01')).toEqual({ ok: false, kind: 'notFound' })
  })
})
