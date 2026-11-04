import { Badge } from '@sami/ui'
import { statusLabels } from '../requisitionStatus'
import type { RequisitionStatus } from '../requisitionStatus'

const colors: Record<RequisitionStatus, string> = {
  not_released: 'gray',
  in_release: 'yellow',
  released: 'green',
  ordered: 'blue',
  deleted: 'red',
}

export function StatusBadge({ status }: { status: RequisitionStatus }) {
  return <Badge color={colors[status]}>{statusLabels[status]}</Badge>
}
