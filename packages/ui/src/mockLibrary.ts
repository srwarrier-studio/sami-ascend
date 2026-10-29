export type MockLibraryItem = { id: string; title: string; description: string; category: string; widget: string; props: object }

type Format = 'number' | 'currency' | 'percent'

const months = ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct']
const points = (labels: string[], values: number[]) => labels.map((label, index) => ({ label, value: values[index] }))
const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

const entry = (id: string, title: string, description: string, category: string, widget: string, props: object): MockLibraryItem => ({
  id,
  title,
  description,
  category,
  widget,
  props: { title, ...props },
})

const kpi = (id: string, title: string, description: string, category: string, measure: string, value: number, valueFormat: Format, delta: number, caption: string, trend: number[]) =>
  entry(id, title, description, category, 'KpiCard', { measure, value, valueFormat, delta, caption, trend })

const gauge = (id: string, title: string, description: string, category: string, measure: string, value: number, target: number, valueFormat: Format, caption: string) =>
  entry(id, title, description, category, 'GaugeChart', { measure, value, target, valueFormat, caption })

const ranked = (id: string, title: string, description: string, category: string, measure: string, valueFormat: Format, labels: string[], values: number[]) =>
  entry(id, title, description, category, 'RankedList', { measure, valueFormat, items: points(labels, values) })

const bars = (id: string, title: string, description: string, category: string, measure: string, valueFormat: Format, labels: string[], values: number[]) =>
  entry(id, title, description, category, 'BarChart', { measure, valueFormat, data: points(labels, values) })

const area = (id: string, title: string, description: string, category: string, measure: string, valueFormat: Format, values: number[]) =>
  entry(id, title, description, category, 'AreaChart', { measure, valueFormat, data: points(months, values) })

const donut = (id: string, title: string, description: string, category: string, measure: string, labels: string[], values: number[], tones: (string | undefined)[] = []) =>
  entry(id, title, description, category, 'DonutChart', { measure, slices: labels.map((label, index) => ({ label, value: values[index], tone: tones[index] })) })

const table = (id: string, title: string, description: string, category: string, columns: { key: string; label: string; format?: string }[], rows: Record<string, string | number>[]) =>
  entry(id, title, description, category, 'DataTable', { columns, rows })

const heat = (id: string, title: string, description: string, category: string, measure: string, rows: string[], columns: string[], value: (row: number, column: number) => number) =>
  entry(id, title, description, category, 'HeatmapChart', {
    measure,
    cells: rows.flatMap((row, r) => columns.map((column, c) => ({ row, column, value: value(r, c) }))),
  })

const yearDays = (base: number) => {
  const end = Date.UTC(2026, 9, 29)
  return Array.from({ length: 365 }, (_, index) => {
    const date = new Date(end - (364 - index) * 86400000)
    const weekend = date.getUTCDay() === 0 || date.getUTCDay() === 6
    return { date: date.toISOString().slice(0, 10), value: Math.round(base * (weekend ? 0.2 : 1) * (0.6 + 0.4 * Math.abs(Math.sin(index / 9)))) }
  })
}

export const mockLibrary: MockLibraryItem[] = [
  kpi('fin-receivables', 'Receivables outstanding', 'Invoice amount not yet collected.', 'Finance', 'receivables', 1840000, 'currency', -0.04, 'vs last month', [2.1, 2.0, 1.95, 1.9, 1.88, 1.84].map((v) => v * 1e6)),
  kpi('fin-collections', 'Collections this month', 'Payments received since the 1st of this month.', 'Finance', 'collections', 2810000, 'currency', 0.07, 'vs last month', [2.2, 2.4, 2.3, 2.6, 2.5, 2.81].map((v) => v * 1e6)),
  gauge('fin-collection-target', 'Collections against target', 'Payments received this month against the collection target.', 'Finance', 'collections', 2810000, 3500000, 'currency', 'this month'),
  bars('fin-ageing', 'Receivables ageing', 'Outstanding invoices grouped by how long they are overdue.', 'Finance', 'receivables', 'currency', ['0-30 days', '31-60 days', '61-90 days', '90+ days'], [920000, 540000, 240000, 140000]),
  entry('fin-cashflow', 'Cash in and out', 'Cash received against cash paid out for each month.', 'Finance', 'LineChart', {
    measure: 'cash',
    valueFormat: 'currency',
    data: points(months, [2.4, 2.6, 2.3, 2.9, 2.7, 3.1].map((v) => v * 1e6)),
    compare: points(months, [2.1, 2.5, 2.4, 2.5, 2.6, 2.7].map((v) => v * 1e6)),
    label: 'Cash in',
    compareLabel: 'Cash out',
  }),
  ranked('fin-overdue', 'Most overdue accounts', 'Accounts with the highest overdue balance.', 'Finance', 'overdue amount', 'currency', ['Kestrel Logistics', 'Alder Construction', 'Meridian Foods', 'Harbor Steel Works', 'Northwind Trading'], [310000, 240000, 180000, 120000, 90000]),
  table('fin-payments', 'Recent payments', 'The latest incoming payments and the invoice they cleared.', 'Finance', [
    { key: 'payment', label: 'Payment' },
    { key: 'invoice', label: 'Invoice' },
    { key: 'status', label: 'Status', format: 'status' },
    { key: 'amount', label: 'Amount', format: 'currency' },
  ], [
    { payment: 'PAY-4102', invoice: 'INV-9001', status: 'Paid', amount: 420000 },
    { payment: 'PAY-4101', invoice: 'INV-8994', status: 'Paid', amount: 215000 },
    { payment: 'PAY-4099', invoice: 'INV-8987', status: 'Open', amount: 180000 },
    { payment: 'PAY-4097', invoice: 'INV-8975', status: 'Paid', amount: 96000 },
  ]),
  donut('fin-expenses', 'Expenses by category', 'How operating expenses are shared between categories.', 'Finance', 'expenses', ['Payroll', 'Rent', 'Utilities', 'Travel', 'Other'], [52, 18, 12, 8, 10]),

  kpi('pur-spend', 'Purchases this month', 'Purchase order value raised since the 1st of this month.', 'Purchase', 'purchases', 4120000, 'currency', 0.05, 'vs last month', [3.6, 3.9, 3.7, 4.0, 3.9, 4.12].map((v) => v * 1e6)),
  kpi('pur-open', 'Open purchase orders', 'Purchase orders not yet fully received.', 'Purchase', 'purchase orders', 38, 'number', -0.08, 'vs last month', [44, 42, 43, 41, 40, 38]),
  area('pur-trend', 'Purchase spend trend', 'Purchase order value for each of the last six months.', 'Purchase', 'purchases', 'currency', [3.6, 3.9, 3.7, 4.0, 3.9, 4.12].map((v) => v * 1e6)),
  ranked('pur-vendors', 'Top vendors', 'Vendors ranked by purchase value this month.', 'Purchase', 'purchases', 'currency', ['Bharat Steel Supply', 'Coastal Polymers', 'Apex Fasteners', 'Delta Packaging', 'Orion Chemicals'], [1240000, 880000, 640000, 410000, 320000]),
  donut('pur-categories', 'Spend by category', 'How purchase value is shared between material groups.', 'Purchase', 'purchases', ['Raw material', 'Packaging', 'Consumables', 'Services'], [58, 16, 14, 12]),
  gauge('pur-ontime', 'On-time delivery', 'Share of purchase order lines delivered by the promised date.', 'Purchase', 'on-time deliveries', 0.91, 0.95, 'percent', 'this month'),
  table('pur-recent', 'Recent purchase orders', 'The latest purchase orders and where they stand.', 'Purchase', [
    { key: 'po', label: 'PO' },
    { key: 'vendor', label: 'Vendor' },
    { key: 'status', label: 'Status', format: 'status' },
    { key: 'amount', label: 'Amount', format: 'currency' },
  ], [
    { po: 'PO-7710', vendor: 'Bharat Steel Supply', status: 'Open', amount: 560000 },
    { po: 'PO-7708', vendor: 'Coastal Polymers', status: 'Paid', amount: 310000 },
    { po: 'PO-7705', vendor: 'Apex Fasteners', status: 'Open', amount: 148000 },
    { po: 'PO-7701', vendor: 'Delta Packaging', status: 'Overdue', amount: 92000 },
  ]),
  entry('pur-by-category-month', 'Spend by category per month', 'Purchase value each month split by material group.', 'Purchase', 'StackedBarChart', {
    measure: 'purchases',
    valueFormat: 'currency',
    series: [
      { name: 'Raw material', data: points(months, [2.1, 2.3, 2.2, 2.4, 2.3, 2.4].map((v) => v * 1e6)) },
      { name: 'Packaging', data: points(months, [0.6, 0.7, 0.6, 0.7, 0.7, 0.7].map((v) => v * 1e6)) },
      { name: 'Other', data: points(months, [0.9, 0.9, 0.9, 0.9, 0.9, 1.0].map((v) => v * 1e6)) },
    ],
  }),

  kpi('inv-value', 'Stock value', 'Value of all stock on hand across warehouses.', 'Inventory', 'stock value', 12600000, 'currency', 0.02, 'vs last month', [11.8, 12.0, 12.1, 12.3, 12.4, 12.6].map((v) => v * 1e6)),
  kpi('inv-low', 'Items below reorder level', 'Materials whose stock has fallen below the reorder level.', 'Inventory', 'items', 14, 'number', 0.17, 'vs last week', [9, 10, 10, 12, 13, 14]),
  gauge('inv-availability', 'Stock availability', 'Share of materials currently in stock against the availability target.', 'Inventory', 'availability', 0.94, 0.98, 'percent', 'this month'),
  bars('inv-warehouses', 'Stock by warehouse', 'Stock value held in each warehouse.', 'Inventory', 'stock value', 'currency', ['Main', 'North', 'Port', 'Transit'], [6200000, 3100000, 2100000, 1200000]),
  donut('inv-groups', 'Stock by material group', 'How stock value is shared between material groups.', 'Inventory', 'stock value', ['Raw material', 'Finished goods', 'Spares', 'Packaging'], [46, 31, 14, 9]),
  ranked('inv-slow', 'Slow-moving materials', 'Materials that have not moved for the longest time.', 'Inventory', 'idle days', 'number', ['Gasket set 40mm', 'Brass fitting 1in', 'Epoxy primer 20L', 'Cable tray 3m', 'Bearing 6204'], [182, 154, 131, 117, 96]),
  entry('inv-movement', 'Receipts and issues', 'Goods received against goods issued for each month.', 'Inventory', 'LineChart', {
    measure: 'quantity',
    data: points(months, [820, 910, 880, 960, 930, 1010]),
    compare: points(months, [790, 860, 900, 910, 940, 980]),
    label: 'Receipts',
    compareLabel: 'Issues',
  }),
  table('inv-reorder', 'Reorder list', 'Materials to reorder soon with their current stock.', 'Inventory', [
    { key: 'material', label: 'Material' },
    { key: 'stock', label: 'In stock', format: 'number' },
    { key: 'level', label: 'Reorder at', format: 'number' },
    { key: 'status', label: 'Status', format: 'status' },
  ], [
    { material: 'Rebar 12mm', stock: 120, level: 200, status: 'Overdue' },
    { material: 'Cement 42.5R', stock: 340, level: 400, status: 'Open' },
    { material: 'PVC conduit', stock: 90, level: 150, status: 'Open' },
    { material: 'Copper wire', stock: 420, level: 300, status: 'Paid' },
  ]),
  heat('inv-heat', 'Goods movement by weekday and hour', 'When goods are received and issued through the week.', 'Inventory', 'movements', weekdays, ['9am', '11am', '1pm', '3pm', '5pm'], (r, c) => 20 + ((r * 7 + c * 11) % 40)),

  kpi('exp-shipments', 'Shipments this month', 'Export shipments dispatched since the 1st of this month.', 'Exports', 'shipments', 46, 'number', 0.09, 'vs last month', [34, 38, 41, 39, 43, 46]),
  kpi('exp-revenue', 'Export revenue', 'Invoiced export value this month.', 'Exports', 'export revenue', 5240000, 'currency', 0.11, 'vs last month', [4.1, 4.4, 4.3, 4.7, 4.9, 5.24].map((v) => v * 1e6)),
  area('exp-trend', 'Export revenue trend', 'Invoiced export value for each of the last six months.', 'Exports', 'export revenue', 'currency', [4.1, 4.4, 4.3, 4.7, 4.9, 5.24].map((v) => v * 1e6)),
  ranked('exp-destinations', 'Top destinations', 'Destination countries ranked by export value.', 'Exports', 'export revenue', 'currency', ['United Arab Emirates', 'Germany', 'United States', 'Singapore', 'Kenya'], [1480000, 1120000, 940000, 710000, 450000]),
  donut('exp-modes', 'Shipments by mode', 'How shipments are shared between sea, air and road.', 'Exports', 'shipments', ['Sea', 'Air', 'Road'], [29, 11, 6]),
  table('exp-transit', 'Shipments in transit', 'Export shipments on their way and when they are due.', 'Exports', [
    { key: 'shipment', label: 'Shipment' },
    { key: 'destination', label: 'Destination' },
    { key: 'status', label: 'Status', format: 'status' },
    { key: 'value', label: 'Value', format: 'currency' },
  ], [
    { shipment: 'EXP-2210', destination: 'Hamburg', status: 'Open', value: 880000 },
    { shipment: 'EXP-2208', destination: 'Jebel Ali', status: 'Open', value: 640000 },
    { shipment: 'EXP-2205', destination: 'Singapore', status: 'Paid', value: 410000 },
    { shipment: 'EXP-2201', destination: 'Mombasa', status: 'Overdue', value: 260000 },
  ]),
  entry('exp-calendar', 'Shipments per day', 'A year calendar showing which days shipments went out.', 'Exports', 'CalendarHeatmapChart', { measure: 'shipments', days: yearDays(4) }),

  kpi('prod-output', 'Units produced today', 'Finished units reported from the shop floor today.', 'Production', 'units', 1840, 'number', 0.03, 'vs yesterday', [1620, 1700, 1650, 1780, 1790, 1840]),
  gauge('prod-oee', 'Equipment effectiveness', 'Overall equipment effectiveness against the target.', 'Production', 'effectiveness', 0.78, 0.85, 'percent', 'this month'),
  entry('prod-plan', 'Output against plan', 'Units produced for each month against the production plan.', 'Production', 'LineChart', {
    measure: 'units',
    data: points(months, [38200, 40100, 39800, 42300, 41900, 44000]),
    compare: points(months, [40000, 40000, 41000, 42000, 43000, 44000]),
    label: 'Produced',
    compareLabel: 'Plan',
  }),
  bars('prod-downtime', 'Downtime by cause', 'Hours of machine stoppage grouped by cause.', 'Production', 'downtime hours', 'number', ['Breakdown', 'Changeover', 'No material', 'Maintenance', 'Other'], [42, 31, 24, 18, 9]),
  donut('prod-scrap', 'Scrap by reason', 'How scrapped units are shared between reasons.', 'Production', 'scrap', ['Material defect', 'Machine setting', 'Operator error', 'Other'], [38, 31, 19, 12], ['negative', undefined, undefined, 'neutral']),
  heat('prod-heat', 'Output by line and shift', 'Units produced on each line in each shift.', 'Production', 'units', ['Line 1', 'Line 2', 'Line 3', 'Line 4'], ['Morning', 'Afternoon', 'Night'], (r, c) => 400 + ((r * 3 + c * 5) % 7) * 60),
  table('prod-orders', 'Open production orders', 'Production orders still running and how far along they are.', 'Production', [
    { key: 'order', label: 'Order' },
    { key: 'item', label: 'Item' },
    { key: 'status', label: 'Status', format: 'status' },
    { key: 'quantity', label: 'Quantity', format: 'number' },
  ], [
    { order: 'PRD-3301', item: 'Valve body A12', status: 'Open', quantity: 1200 },
    { order: 'PRD-3299', item: 'Flange 6in', status: 'Open', quantity: 800 },
    { order: 'PRD-3294', item: 'Pump casing P4', status: 'Overdue', quantity: 340 },
    { order: 'PRD-3290', item: 'Bracket set', status: 'Paid', quantity: 2500 },
  ]),
]
