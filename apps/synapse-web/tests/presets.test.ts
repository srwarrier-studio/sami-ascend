import { listPresets } from '../src/boards/presets'
import { fixtureEntries } from '../src/catalog/fixtures'
import type { CatalogEntry } from '../src/catalog/catalogClient'

const entry = (id: string) => ({ id, title: id, description: '', category: 'Sales', widget: 'KpiCard' }) as CatalogEntry

describe('listing presets', () => {
  it('lists every preset when the whole catalog is loaded', () => {
    const catalog = fixtureEntries
    const all = listPresets(catalog)
    expect(all.map((preset) => preset.name)).toEqual(['Sales overview', 'Customers and materials', 'Daily pulse'])
    all.forEach((preset) => preset.catalogIds.forEach((id) => expect(catalog.some((item) => item.id === id)).toBe(true)))
  })

  it('drops catalog ids the catalog does not have', () => {
    const [preset] = listPresets([entry('sales-today'), entry('day-sales')])
    expect(preset.catalogIds).toEqual(['sales-today', 'day-sales'])
  })

  it('does not list a preset left with no widgets', () => {
    expect(listPresets([entry('top-customers')]).map((preset) => preset.name)).toEqual(['Customers and materials'])
    expect(listPresets([])).toEqual([])
  })
})
