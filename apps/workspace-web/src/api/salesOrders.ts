import { WORKSPACE_URL } from '../config'

export type NewOrderItem = { material: string; quantity: string; quantity_unit: string }

export type NewOrder = {
  sales_order_type: string
  sold_to_party: string
  transaction_currency: string
  requested_delivery_date: string | null
  items: NewOrderItem[]
}

export type ErrorDetail = { code: string; target: string; message: string }

export type RequestStatus = 'queued' | 'sending' | 'unknown' | 'failed' | 'posted' | 'rejected'

export type OrderRequest = {
  id: string
  status: RequestStatus
  attempts: number
  created_at: string
  message: string | null
  order: NewOrder
}

export type CreateResult =
  | { ok: true; salesOrder: string }
  | { ok: false; kind: 'validation'; details: ErrorDetail[] }
  | { ok: false; kind: 'queued' | 'unknown'; request: OrderRequest }
  | { ok: false; kind: 'notSaved' | 'unavailable' | 'failed' }

export type SalesOrderClient = {
  create: (order: NewOrder) => Promise<CreateResult>
  openRequests: () => Promise<OrderRequest[]>
}

const base = `${WORKSPACE_URL}/v1/workspace`

export const salesOrderClient: SalesOrderClient = {
  async create(order) {
    try {
      const response = await fetch(`${base}/sales-orders`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(order),
      })
      if (response.status === 201) {
        const body = await response.json()
        return { ok: true, salesOrder: body.sales_order }
      }
      if (response.status === 202) {
        const request: OrderRequest = await response.json()
        if (request.status === 'queued' || request.status === 'unknown') {
          return { ok: false, kind: request.status, request }
        }
      }
      if (response.status === 422) {
        const body = await response.json()
        if (body.code === 'VALIDATION_FAILED') {
          return { ok: false, kind: 'validation', details: body.details }
        }
      }
      if (response.status === 503) {
        const body = await response.json().catch(() => ({}))
        return { ok: false, kind: body.code === 'STORE_UNAVAILABLE' ? 'notSaved' : 'unavailable' }
      }
      return { ok: false, kind: 'failed' }
    } catch {
      return { ok: false, kind: 'failed' }
    }
  },
  async openRequests() {
    const response = await fetch(`${base}/sales-order-requests?open=true`, { credentials: 'include' })
    if (!response.ok) throw new Error(`open requests failed: ${response.status}`)
    return (await response.json()).requests
  },
}
