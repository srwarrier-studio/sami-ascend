export type MenuPath =
  | '/sales-orders'
  | '/sales-orders/new'
  | '/purchase-requisitions'
  | '/purchase-requisitions/new'

export type MenuEntry = { label: string; path: MenuPath; roles: string[] }

export const menu: MenuEntry[] = [
  { label: 'Sales orders', path: '/sales-orders', roles: ['sales'] },
  { label: 'New sales order', path: '/sales-orders/new', roles: ['sales'] },
  { label: 'Purchase requisitions', path: '/purchase-requisitions', roles: ['purchase', 'management'] },
  { label: 'New requisition', path: '/purchase-requisitions/new', roles: ['purchase'] },
]

export const allowedEntries = (roles: string[]) =>
  menu.filter((entry) => entry.roles.some((role) => roles.includes(role)))
