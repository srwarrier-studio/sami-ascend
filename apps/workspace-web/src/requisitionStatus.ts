import type { Requisition, RequisitionItem } from './api/purchaseRequisitions'

export type RequisitionStatus = 'not_released' | 'in_release' | 'released' | 'ordered' | 'deleted'

export const statusLabels: Record<RequisitionStatus, string> = {
  not_released: 'Not released',
  in_release: 'In release',
  released: 'Released',
  ordered: 'Ordered',
  deleted: 'Deleted',
}

const progress: RequisitionStatus[] = ['not_released', 'in_release', 'released', 'ordered']

export const itemStatus = (item: RequisitionItem): RequisitionStatus =>
  item.deleted ? 'deleted' : item.ordered ? 'ordered' : item.release_status

export const requisitionStatus = (requisition: Requisition): RequisitionStatus => {
  const live = requisition.items.filter((item) => !item.deleted)
  if (live.length === 0) return 'deleted'
  const ranks = live.map((item) => progress.indexOf(itemStatus(item)))
  return progress[Math.min(...ranks)]
}

export const canBeReleased = (item: RequisitionItem) =>
  !item.deleted && !item.ordered && item.release_status !== 'released'
