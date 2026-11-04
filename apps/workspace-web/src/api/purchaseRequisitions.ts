import { WORKSPACE_URL } from '../config'
import type { ErrorDetail } from './salesOrders'

export type ReleaseWord = 'not_released' | 'in_release' | 'released'

export type RequisitionItem = {
  item: string
  material: string
  text: string
  plant: string
  company_code: string
  quantity: string
  unit: string
  net_amount: string
  currency: string
  delivery_date: string
  release_status: ReleaseWord
  release_status_code: string
  ordered: boolean
  deleted: boolean
  purchase_order: string
}

export type Requisition = {
  purchase_requisition: string
  description: string
  created_by_user: string
  created_on: string | null
  total_net_amount: string
  items: RequisitionItem[]
}

export type RequisitionPage = { requisitions: Requisition[]; total: number }

export type NewRequisitionItem = {
  material: string
  plant: string
  quantity: string
  unit: string
  delivery_date: string
  text?: string
}

export type NewRequisition = { description: string; items: NewRequisitionItem[] }

export type RequisitionResult =
  | { ok: true; requisition: Requisition }
  | { ok: false; kind: 'validation'; details: ErrorDetail[] }
  | { ok: false; kind: 'notAllowed' | 'notFound' | 'unavailable' | 'failed' }

export type PurchaseRequisitionClient = {
  list: (top: number, skip: number) => Promise<RequisitionPage>
  get: (number: string) => Promise<Requisition | null>
  create: (requisition: NewRequisition) => Promise<RequisitionResult>
  release: (number: string, releaseCode: string, item?: string) => Promise<RequisitionResult>
}

const base = `${WORKSPACE_URL}/v1/workspace/purchase-requisitions`

const send = (url: string, method: string, body?: unknown) =>
  fetch(url, {
    method,
    credentials: 'include',
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })

async function result(response: Response, success: number): Promise<RequisitionResult> {
  if (response.status === success) return { ok: true, requisition: await response.json() }
  if (response.status === 422) {
    const body = await response.json().catch(() => ({}))
    if (body.code === 'VALIDATION_FAILED') return { ok: false, kind: 'validation', details: body.details }
  }
  if (response.status === 403) return { ok: false, kind: 'notAllowed' }
  if (response.status === 404) return { ok: false, kind: 'notFound' }
  if (response.status === 503) return { ok: false, kind: 'unavailable' }
  return { ok: false, kind: 'failed' }
}

export const purchaseRequisitionClient: PurchaseRequisitionClient = {
  async list(top, skip) {
    const response = await send(`${base}?top=${top}&skip=${skip}`, 'GET')
    if (!response.ok) throw new Error(`list failed: ${response.status}`)
    return response.json()
  },
  async get(number) {
    const response = await send(`${base}/${encodeURIComponent(number)}`, 'GET')
    if (response.status === 404) return null
    if (!response.ok) throw new Error(`get failed: ${response.status}`)
    return response.json()
  },
  async create(requisition) {
    try {
      return await result(await send(base, 'POST', requisition), 201)
    } catch {
      return { ok: false, kind: 'failed' }
    }
  },
  async release(number, releaseCode, item) {
    try {
      const body = item ? { release_code: releaseCode, item } : { release_code: releaseCode }
      return await result(await send(`${base}/${encodeURIComponent(number)}/release`, 'POST', body), 200)
    } catch {
      return { ok: false, kind: 'failed' }
    }
  },
}
