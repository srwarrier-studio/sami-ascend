export const days = [
  { label: 'Mon', value: 100 },
  { label: 'Tue', value: 250 },
]

export const samples: Record<string, object> = {
  KpiCard: { title: 'Today', value: 125000, valueFormat: 'currency', delta: 0.05, caption: 'vs yesterday', trend: [1, 3, 2, 4] },
  RankedList: { title: 'Top customers', items: days, valueFormat: 'number' },
  DataTable: {
    title: 'Recent high-value sales',
    columns: [
      { key: 'order', label: 'Order' },
      { key: 'amount', label: 'Amount', format: 'currency' },
    ],
    rows: [{ order: '0000012031', amount: 500000 }],
  },
  DonutChart: { title: 'Invoice status', slices: [{ label: 'Paid', value: 58, tone: 'positive' }, { label: 'Open', value: 42 }] },
  GaugeChart: { title: 'Month target', value: 72, target: 100, caption: 'this month' },
  AreaChart: { data: days, title: 'Cumulative sales' },
  StackedBarChart: { title: 'Sales by status', series: [{ name: 'Paid', data: days }, { name: 'Open', data: days }], layout: 'stacked' },
  CalendarHeatmapChart: { title: 'Sales per day', days: [{ date: '2026-10-01', value: 1 }, { date: '2026-10-02', value: 4 }] },
  HeatmapChart: { title: 'Sales by hour', cells: [{ row: 'Mon', column: '9', value: 1 }, { row: 'Mon', column: '10', value: 4 }] },
  LineChart: { data: days, title: 'Day sales' },
  BarChart: { data: days, title: 'By customer' },
}
