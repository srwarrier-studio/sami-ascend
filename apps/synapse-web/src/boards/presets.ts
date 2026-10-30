import type { CatalogEntry } from '../catalog/catalogClient'

export type Preset = { id: string; name: string; description: string; catalogIds: string[] }

const presets: Preset[] = [
  {
    id: 'sales-overview',
    name: 'Sales overview',
    description: 'Today, this month and this year at a glance, with the month target.',
    catalogIds: ['sales-today', 'sales-month', 'sales-year', 'orders-month', 'month-on-month', 'day-sales', 'status-split', 'month-target'],
  },
  {
    id: 'customers-and-materials',
    name: 'Customers and materials',
    description: 'Who buys, what sells and the biggest sales.',
    catalogIds: ['top-customers', 'top-materials', 'high-value-sales'],
  },
  {
    id: 'daily-pulse',
    name: 'Daily pulse',
    description: 'A short board to check every morning.',
    catalogIds: ['sales-today', 'orders-month', 'day-sales', 'month-target'],
  },
]

export const listPresets = (catalog: CatalogEntry[]): Preset[] =>
  presets
    .map((preset) => ({ ...preset, catalogIds: preset.catalogIds.filter((id) => catalog.some((entry) => entry.id === id)) }))
    .filter((preset) => preset.catalogIds.length > 0)
