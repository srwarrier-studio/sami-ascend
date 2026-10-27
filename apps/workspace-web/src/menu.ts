export type MenuPath = '/sales-orders' | '/sales-orders/new'

export type MenuEntry = { label: string; path: MenuPath; roles: string[] }

export const menu: MenuEntry[] = [
  { label: 'Sales orders', path: '/sales-orders', roles: ['sales'] },
  { label: 'New sales order', path: '/sales-orders/new', roles: ['sales'] },
]

export const allowedEntries = (roles: string[]) =>
  menu.filter((entry) => entry.roles.some((role) => roles.includes(role)))
