import { useState } from 'react'
import { ActionIcon, allowedSizes, ArrowsOutSimpleIcon, Button, Group, PageBar, PageHeader, PencilSimpleIcon, PlusIcon, registry, WidgetCell, WidgetGrid, SparkleIcon, Stack } from '../src'
import type { PageBarConfig, SizeName } from '../src'

const months = [
  ['Nov', 2.1],
  ['Dec', 2.3],
  ['Jan', 2.2],
  ['Feb', 2.6],
  ['Mar', 2.8],
  ['Apr', 2.7],
  ['May', 3.0],
  ['Jun', 2.9],
  ['Jul', 3.1],
  ['Aug', 3.0],
  ['Sep', 3.2],
  ['Oct', 3.4],
].map(([label, value]) => ({ label: String(label), value: Number(value) * 1000000 }))

const days = Array.from({ length: 14 }, (_, index) => ({
  label: String(index + 15),
  value: Math.round((1.4 + index * 0.03 + Math.sin(index * 0.9) * 0.35) * 1000000),
}))

const lastMonth = days.map((point, index) => ({
  label: point.label,
  value: Math.round((1.2 + index * 0.015 + Math.sin(index * 0.7 + 1) * 0.3) * 1000000),
}))

const cumulative = days.map((point, index) => ({
  label: point.label,
  value: days.slice(0, index + 1).reduce((sum, day) => sum + day.value, 0),
}))

const byStatus = [
  { name: 'Paid', data: [['Aug', 1.9], ['Sep', 2.1], ['Oct', 2.0]] },
  { name: 'Open', data: [['Aug', 0.8], ['Sep', 0.8], ['Oct', 1.0]] },
  { name: 'Overdue', data: [['Aug', 0.3], ['Sep', 0.3], ['Oct', 0.4]] },
].map(({ name, data }) => ({ name, data: data.map(([label, value]) => ({ label: String(label), value: Number(value) * 1000000 })) }))

const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
const hours = ['9am', '10am', '11am', '12pm', '1pm', '2pm']
const busy = weekdays.flatMap((row, rowIndex) =>
  hours.map((column, columnIndex) => ({ row, column, value: Math.round(40 + 30 * Math.sin(columnIndex * 0.9 + rowIndex) + rowIndex * 4) })),
)

const yearOfSales = Array.from({ length: 360 }, (_, index) => {
  const time = Date.UTC(2025, 10, 3) + index * 86400000
  const weekday = (new Date(time).getUTCDay() + 6) % 7
  const season = 1 + 0.35 * Math.sin((index / 360) * Math.PI * 2 + 1)
  const noise = 0.75 + 0.5 * Math.abs(Math.sin(index * 12.9898) * 43758.5453 % 1)
  return { date: new Date(time).toISOString().slice(0, 10), value: Math.round((weekday < 5 ? 90000 : 18000) * season * noise) }
})

const customers = [
  { label: 'Northwind Trading', value: 412000 },
  { label: 'Harbor Steel Works', value: 368000 },
  { label: 'Alder Construction', value: 301000 },
  { label: 'Kestrel Logistics', value: 244000 },
  { label: 'Meridian Foods', value: 197000 },
]

const materials = [
  { label: 'Rebar 12mm', value: 520000 },
  { label: 'Cement 42.5R', value: 448000 },
  { label: 'Steel plate 8mm', value: 371000 },
  { label: 'PVC conduit', value: 255000 },
  { label: 'Copper wire', value: 213000 },
]

const sales = [
  { invoice: 'INV-20418', customer: 'Northwind Trading', status: 'Paid', amount: 84200 },
  { invoice: 'INV-20411', customer: 'Harbor Steel Works', status: 'Open', amount: 71950 },
  { invoice: 'INV-20407', customer: 'Alder Construction', status: 'Overdue', amount: 66300 },
  { invoice: 'INV-20399', customer: 'Kestrel Logistics', status: 'Paid', amount: 58780 },
]

const salesColumns = [
  { key: 'invoice', label: 'Invoice', format: 'text' },
  { key: 'customer', label: 'Customer', format: 'text' },
  { key: 'status', label: 'Status', format: 'status' },
  { key: 'amount', label: 'Amount', format: 'currency' },
]

type Row = { widgets: { name: string; props: object }[] }

export const dashboardRows: Row[] = [
  {
    widgets: [
      { name: 'KpiCard', props: { title: 'Sales this month', measure: 'sales', value: 3400000, valueFormat: 'currency', delta: 0.062, caption: 'vs last month', trend: [2.1, 2.3, 2.2, 2.6, 2.8, 2.7, 3.0, 3.4], info: 'Net invoiced sales since the 1st of this month.' } },
      { name: 'KpiCard', props: { title: 'Invoices', measure: 'invoices', value: 1284, delta: 0.031, caption: 'Raised this month', trend: [1100, 1150, 1120, 1210, 1180, 1250, 1284] } },
      { name: 'KpiCard', props: { title: 'Active customers', measure: 'customers', value: 312, caption: '9 new this month', trend: [290, 296, 301, 303, 308, 312] } },
      { name: 'KpiCard', props: { title: 'Average invoice', measure: 'the average invoice value', value: 2648, valueFormat: 'currency', delta: -0.014, caption: 'vs last month', trend: [2750, 2700, 2720, 2680, 2660, 2648] } },
    ],
  },
  {
    widgets: [
      { name: 'LineChart', props: { title: 'Day sales', measure: 'sales', data: days, compare: lastMonth, label: 'This month', compareLabel: 'Last month', valueFormat: 'currency' } },
      { name: 'BarChart', props: { title: 'Month-on-month sales', measure: 'sales', data: months, valueFormat: 'currency' } },
    ],
  },
  {
    widgets: [
      { name: 'DonutChart', props: { title: 'Invoice status', measure: 'invoices', slices: [{ label: 'Paid', value: 58, tone: 'positive' }, { label: 'Open', value: 27 }, { label: 'Overdue', value: 15, tone: 'negative' }] } },
      { name: 'GaugeChart', props: { title: 'Month target', measure: 'sales', value: 3400000, target: 5000000, valueFormat: 'currency', caption: 'this month' } },
      { name: 'RankedList', props: { title: 'Top customers', measure: 'sales', items: customers, valueFormat: 'currency' } },
      { name: 'RankedList', props: { title: 'Top materials', measure: 'sales', items: materials, valueFormat: 'currency' } },
    ],
  },
  {
    widgets: [
      { name: 'AreaChart', props: { title: 'Cumulative sales', measure: 'sales', data: cumulative, valueFormat: 'currency' } },
      { name: 'StackedBarChart', props: { title: 'Sales by invoice status', measure: 'sales', series: byStatus, valueFormat: 'currency' } },
    ],
  },
  {
    widgets: [
      { name: 'CalendarHeatmapChart', props: { title: 'Sales per day', measure: 'sales', days: yearOfSales, valueFormat: 'currency' } },
    ],
  },
  {
    widgets: [
      { name: 'HeatmapChart', props: { title: 'Orders by weekday and hour', measure: 'orders', cells: busy } },
    ],
  },
  {
    widgets: [
      { name: 'DataTable', props: { title: 'Recent high-value sales', columns: salesColumns, rows: sales } },
    ],
  },
]

const nextSize = (resized: Record<number, SizeName>, position: number, widget: string) => {
  const allowed = allowedSizes(widget)
  const next = allowed[(allowed.indexOf(resized[position] ?? allowed[0]) + 1) % allowed.length]
  return { ...resized, [position]: next }
}

type DashboardDemoProps = { config: PageBarConfig; onConfigChange: (config: PageBarConfig) => void }

export function DashboardDemo({ config, onConfigChange }: DashboardDemoProps) {
  const [editing, setEditing] = useState(false)
  const [resized, setResized] = useState<Record<number, SizeName>>({})
  const [tabs, setTabs] = useState([
    { id: 'sales', name: 'Sales overview' },
    { id: 'customers', name: 'Customers' },
    { id: 'materials', name: 'Materials' },
    { id: 'quality', name: 'Quality' },
  ])
  const [activeId, setActiveId] = useState('sales')
  return (
    <>
      <PageHeader
        title={tabs.find((tab) => tab.id === activeId)?.name ?? ''}
        breadcrumb={['Boards']}
        editing={editing}
        onTitleChange={(name) => setTabs(tabs.map((tab) => (tab.id === activeId ? { ...tab, name } : tab)))}
        actions={
          <Group>
            <Button variant={editing ? 'filled' : 'default'} leftSection={<PencilSimpleIcon size={16} />} onClick={() => setEditing(!editing)}>
              {editing ? 'Done' : 'Edit'}
            </Button>
            <Button variant="light" leftSection={<SparkleIcon size={16} weight="fill" />}>
              AI Mode
            </Button>
            <Button leftSection={<PlusIcon size={16} />}>Add widget</Button>
          </Group>
        }
      />
      <Stack p="md" pb={80}>
        <WidgetGrid>
          {dashboardRows.flatMap((row) => row.widgets).map((widget, position) => (
            <WidgetCell key={position} widget={widget.name} size={resized[position]} editing={editing}>
              {editing && allowedSizes(widget.name).length > 1 && (
                <ActionIcon
                  variant="light"
                  size="sm"
                  aria-label={`Resize ${widget.name}`}
                  style={{ position: 'absolute', top: 4, right: 4, zIndex: 2 }}
                  onClick={() => setResized(nextSize(resized, position, widget.name))}
                >
                  <ArrowsOutSimpleIcon size={14} />
                </ActionIcon>
              )}
              {registry.render(widget.name, widget.props)}
            </WidgetCell>
          ))}
        </WidgetGrid>
      </Stack>
      <PageBar
        tabs={tabs}
        activeId={activeId}
        config={config}
        onSelect={setActiveId}
        onAdd={() => setTabs([...tabs, { id: `board-${tabs.length + 1}`, name: `Board ${tabs.length + 1}` }])}
        onConfigChange={onConfigChange}
      />
    </>
  )
}
