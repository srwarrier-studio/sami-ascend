import { salesOrderClient } from '../src/api/salesOrders'
import type { NewOrder } from '../src/api/salesOrders'

const order: NewOrder = {
  sales_order_type: 'OR',
  sold_to_party: '0000100001',
  transaction_currency: 'INR',
  requested_delivery_date: null,
  items: [{ material: 'RM-1001', quantity: '5', quantity_unit: 'KG' }],
}

const respond = (status: number, body: unknown) =>
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status })))

afterEach(() => vi.unstubAllGlobals())

describe('create', () => {
  it('returns the order number on 201 and posts json with the cookie', async () => {
    respond(201, { sales_order: '0000012345' })
    expect(await salesOrderClient.create(order)).toEqual({ ok: true, salesOrder: '0000012345' })
    const [url, init] = vi.mocked(fetch).mock.calls[0]
    expect(url).toBe('http://localhost:8002/v1/workspace/sales-orders')
    expect(init).toMatchObject({ method: 'POST', credentials: 'include', body: JSON.stringify(order) })
  })

  it('returns the details on 422', async () => {
    const details = [{ code: 'CUSTOMER_UNKNOWN', target: 'SoldToParty', message: 'No such customer' }]
    respond(422, { code: 'VALIDATION_FAILED', details })
    expect(await salesOrderClient.create(order)).toEqual({ ok: false, kind: 'validation', details })
  })

  it('treats another 422 as failed', async () => {
    respond(422, { code: 'INVALID_QUERY' })
    expect(await salesOrderClient.create(order)).toEqual({ ok: false, kind: 'failed' })
  })

  it('returns unavailable on 503', async () => {
    respond(503, { code: 'SAP_UNAVAILABLE' })
    expect(await salesOrderClient.create(order)).toEqual({ ok: false, kind: 'unavailable' })
  })

  it('returns failed on a network error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('network')))
    expect(await salesOrderClient.create(order)).toEqual({ ok: false, kind: 'failed' })
  })
})
