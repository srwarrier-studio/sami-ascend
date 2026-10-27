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

export type CreateResult =
  | { ok: true; salesOrder: string }
  | { ok: false; kind: 'validation'; details: ErrorDetail[] }
  | { ok: false; kind: 'unavailable' | 'failed' }

export type SalesOrderClient = {
  create: (order: NewOrder) => Promise<CreateResult>
}

export const salesOrderClient: SalesOrderClient = {
  async create(order) {
    try {
      const response = await fetch(`${WORKSPACE_URL}/v1/workspace/sales-orders`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(order),
      })
      if (response.status === 201) {
        const body = await response.json()
        return { ok: true, salesOrder: body.sales_order }
      }
      if (response.status === 422) {
        const body = await response.json()
        if (body.code === 'VALIDATION_FAILED') {
          return { ok: false, kind: 'validation', details: body.details }
        }
      }
      if (response.status === 503) return { ok: false, kind: 'unavailable' }
      return { ok: false, kind: 'failed' }
    } catch {
      return { ok: false, kind: 'failed' }
    }
  },
}
