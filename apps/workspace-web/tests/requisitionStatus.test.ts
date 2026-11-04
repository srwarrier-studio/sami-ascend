import type { Requisition, RequisitionItem } from '../src/api/purchaseRequisitions'
import { canBeReleased, itemStatus, requisitionStatus } from '../src/requisitionStatus'

const item = (changes: Partial<RequisitionItem> = {}): RequisitionItem => ({
  item: '10', material: 'RM-1001', text: '', plant: '1000', company_code: 'INA1', quantity: '5.000', unit: 'KG',
  net_amount: '100.00', currency: 'INR', delivery_date: '2026-12-01', release_status: 'released',
  release_status_code: '03', ordered: false, deleted: false, purchase_order: '', ...changes,
})

const requisition = (...items: RequisitionItem[]): Requisition => ({
  purchase_requisition: '10000000', description: '', created_by_user: 'X', created_on: null, total_net_amount: '0', items,
})

describe('an item', () => {
  it.each([
    [{ release_status: 'not_released' }, 'not_released'],
    [{ release_status: 'in_release' }, 'in_release'],
    [{}, 'released'],
    [{ ordered: true }, 'ordered'],
    [{ deleted: true, ordered: true }, 'deleted'],
  ] as const)('with %j is %s', (changes, status) => {
    expect(itemStatus(item(changes))).toBe(status)
  })

  it('can be released only while not released, ordered or deleted', () => {
    expect(canBeReleased(item({ release_status: 'not_released' }))).toBe(true)
    expect(canBeReleased(item({ release_status: 'in_release' }))).toBe(true)
    expect(canBeReleased(item())).toBe(false)
    expect(canBeReleased(item({ ordered: true }))).toBe(false)
    expect(canBeReleased(item({ deleted: true, release_status: 'not_released' }))).toBe(false)
  })
})

describe('a requisition', () => {
  it('shows the least advanced live item', () => {
    expect(requisitionStatus(requisition(item({ ordered: true }), item({ release_status: 'in_release' })))).toBe('in_release')
    expect(requisitionStatus(requisition(item(), item({ ordered: true })))).toBe('released')
    expect(requisitionStatus(requisition(item({ release_status: 'not_released' }), item()))).toBe('not_released')
  })

  it('ignores deleted items', () => {
    expect(requisitionStatus(requisition(item({ deleted: true, release_status: 'not_released' }), item({ ordered: true })))).toBe('ordered')
  })

  it('is deleted when every item is', () => {
    expect(requisitionStatus(requisition(item({ deleted: true })))).toBe('deleted')
  })
})
