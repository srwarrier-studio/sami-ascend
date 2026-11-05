import { ClipboardTextIcon, FileTextIcon, HouseIcon, PlusIcon } from '@sami/ui'
import type { NavItem } from '@sami/ui'
import { allowedEntries } from './menu'
import type { MenuPath } from './menu'

export type NavPath = '/' | MenuPath
export type NavEntry = { key: string; label: string; path: NavPath; icon: NavItem['icon'] }

const icons: Record<MenuPath, NavItem['icon']> = {
  '/sales-orders': FileTextIcon,
  '/sales-orders/new': PlusIcon,
  '/purchase-requisitions': ClipboardTextIcon,
  '/purchase-requisitions/new': PlusIcon,
}

export const navEntries = (roles: string[]): NavEntry[] => [
  { key: 'home', label: 'Home', path: '/', icon: HouseIcon },
  ...allowedEntries(roles).map((entry) => ({ key: entry.path, label: entry.label, path: entry.path, icon: icons[entry.path] })),
]

const covers = (path: NavPath, current: string) => current === path || (path !== '/' && current.startsWith(`${path}/`))

export const activePath = (entries: NavEntry[], current: string): NavPath | null =>
  entries
    .filter((entry) => covers(entry.path, current))
    .reduce<NavPath | null>((best, entry) => (best === null || entry.path.length > best.length ? entry.path : best), null)

export const roleLabel = (roles: string[]) => (roles.length ? roles[0].charAt(0).toUpperCase() + roles[0].slice(1) : '')
