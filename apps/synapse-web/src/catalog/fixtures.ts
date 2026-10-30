import type { CatalogEntry } from './catalogClient'

type Fixture = { entry: CatalogEntry; props: object }

const kpi = (id: string, title: string, value: number, description: string, category = 'Sales'): Fixture => ({
  entry: { id, title, description, category, widget: 'KpiCard' },
  props: { title, measure: 'sales', value, valueFormat: 'currency', delta: 0.0625, caption: 'vs last period' },
})

const ranked = (id: string, title: string, description: string, category: string, items: [string, number][]): Fixture => ({
  entry: { id, title, description, category, widget: 'RankedList' },
  props: { title, measure: 'sales', valueFormat: 'currency', items: items.map(([label, value]) => ({ label, value })) },
})

export const fixtures: Fixture[] = [
  kpi('sales-today', 'Sales today', 120000, 'Net sales invoiced today against yesterday.'),
  kpi('sales-month', 'Sales this month', 3400000, 'Net sales since the 1st of this month against last month.'),
  kpi('stock-value', 'Stock value', 9800000, 'Value of stock on hand.', 'Inventory'),
  ranked('top-customers', 'Top customers', 'Customers ranked by net sales this month.', 'Sales', [['Acme Ltd', 900000], ['Globex', 650000]]),
  ranked('top-materials', 'Top materials', 'Materials ranked by net sales this month.', 'Inventory', [['Steel plate', 700000], ['Copper wire', 420000]]),
  {
    entry: { id: 'day-sales', title: 'Day sales', description: 'Net sales for each day of this month, with last month behind it.', category: 'Sales', widget: 'LineChart' },
    props: {
      title: 'Day sales',
      measure: 'sales',
      valueFormat: 'currency',
      data: [{ label: '1', value: 100000 }, { label: '2', value: 120000 }],
      compare: [{ label: '1', value: 90000 }, { label: '2', value: 95000 }],
      label: 'This month',
      compareLabel: 'Last month',
    },
  },
]

export const fixtureEntries = fixtures.map(({ entry }) => entry)
