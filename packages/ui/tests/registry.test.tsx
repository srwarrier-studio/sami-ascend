import { render } from '@testing-library/react'
import { registry, UiProvider, workspacePalette } from '../src'

const days = [
  { label: 'Mon', value: 100 },
  { label: 'Tue', value: 250 },
]

const samples: Record<string, object> = {
  KpiCard: { title: 'Today', value: 125000, valueFormat: 'currency', delta: 0.05, caption: 'vs yesterday' },
  RankedList: { title: 'Top customers', items: days, valueFormat: 'number' },
  DataTable: {
    title: 'Recent high-value sales',
    columns: [
      { key: 'order', label: 'Order' },
      { key: 'amount', label: 'Amount', format: 'currency' },
    ],
    rows: [{ order: '0000012031', amount: 500000 }],
  },
  LineChart: { data: days, title: 'Day sales' },
  BarChart: { data: days, title: 'By customer' },
}

function show(name: string, props: unknown) {
  return render(<UiProvider palette={workspacePalette}>{registry.render(name, props)}</UiProvider>)
}

function hasFunctionProperty(value: unknown): boolean {
  if (typeof value === 'function') return true
  if (Array.isArray(value)) return value.some(hasFunctionProperty)
  if (value && typeof value === 'object') return Object.values(value).some(hasFunctionProperty)
  return false
}

describe('registry description', () => {
  const described = registry.describe()

  it('lists every name once with a description', () => {
    const names = described.map((entry) => entry.name)
    expect(new Set(names).size).toBe(names.length)
    expect(names.sort()).toEqual(Object.keys(samples).sort())
    for (const entry of described) expect(entry.description.length).toBeGreaterThan(0)
  })

  it('has JSON schemas without functions', () => {
    for (const entry of described) {
      expect(hasFunctionProperty(entry.schema)).toBe(false)
      expect(JSON.parse(JSON.stringify(entry.schema))).toEqual(entry.schema)
    }
  })

  it('gives every widget size hints', () => {
    for (const { size } of described) {
      expect(size.minW).toBeLessThanOrEqual(size.defaultW)
      expect(size.minH).toBeLessThanOrEqual(size.defaultH)
    }
  })
})

describe('registry render with valid props', () => {
  it.each(Object.entries(samples))('renders %s', (name, props) => {
    const { queryByText } = show(name, props)
    expect(queryByText(`Cannot show widget ${name}`)).toBeNull()
  })

  it('formats KpiCard and DataTable values', () => {
    expect(show('KpiCard', samples.KpiCard).getByText('₹1,25,000')).toBeInTheDocument()
    expect(show('DataTable', samples.DataTable).getByText('₹5,00,000')).toBeInTheDocument()
  })

  it('renders a LineChart with a compare series and its legend', () => {
    const points = [
      { label: 'Mon', value: 1 },
      { label: 'Tue', value: 2 },
    ]
    const { container } = show('LineChart', { data: points, compare: points, compareLabel: 'Last week' })
    expect(container.querySelector('.ts-chart__legend')?.textContent).toContain('Last week')
  })

  it('ignores unknown props', () => {
    const { queryByText } = show('KpiCard', { ...samples.KpiCard, surprise: 'x' })
    expect(queryByText('Cannot show widget KpiCard')).toBeNull()
  })
})

describe('registry render with bad input', () => {
  it('shows the fallback for wrong types', () => {
    expect(show('KpiCard', { title: 'Today', value: 'lots' }).getByText('Cannot show widget KpiCard')).toBeInTheDocument()
  })

  it('shows the fallback for missing required props', () => {
    expect(show('RankedList', {}).getByText('Cannot show widget RankedList')).toBeInTheDocument()
  })

  it('shows the fallback for an unknown name', () => {
    expect(show('Nope', {}).getByText('Cannot show widget Nope')).toBeInTheDocument()
  })

  it('shows the fallback for null props and inherited names', () => {
    expect(show('KpiCard', null).getByText('Cannot show widget KpiCard')).toBeInTheDocument()
    expect(show('toString', {}).getByText('Cannot show widget toString')).toBeInTheDocument()
  })
})
