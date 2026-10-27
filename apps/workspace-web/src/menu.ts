export type MenuEntry = { label: string; path: '/sales-orders'; roles: string[] }

export const menu: MenuEntry[] = [{ label: 'Sales orders', path: '/sales-orders', roles: ['sales'] }]

export const allowedEntries = (roles: string[]) =>
  menu.filter((entry) => entry.roles.some((role) => roles.includes(role)))
