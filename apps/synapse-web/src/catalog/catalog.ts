import type { PeriodSales, SalesData } from '../data/salesData'

export type CatalogEntry = {
  id: string
  title: string
  description: string
  widget: string
  load: (data: SalesData) => Promise<object>
}

const delta = (sales: PeriodSales) => (sales.netAmount - sales.previousNetAmount) / sales.previousNetAmount

const salesKpi = (title: string, caption: string, read: (data: SalesData) => Promise<PeriodSales>) => async (data: SalesData) => {
  const sales = await read(data)
  return { title, measure: 'sales', value: sales.netAmount, valueFormat: 'currency', delta: delta(sales), caption, trend: sales.trend }
}

const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

export const catalog: CatalogEntry[] = [
  {
    id: 'sales-today',
    title: 'Sales today',
    description: 'Net sales invoiced today against yesterday.',
    widget: 'KpiCard',
    load: salesKpi('Sales today', 'vs yesterday', (data) => data.today()),
  },
  {
    id: 'sales-month',
    title: 'Sales this month',
    description: 'Net sales since the 1st of this month against the same days last month.',
    widget: 'KpiCard',
    load: salesKpi('Sales this month', 'vs last month', (data) => data.monthToDate()),
  },
  {
    id: 'sales-year',
    title: 'Sales this year',
    description: 'Net sales since the start of the year against the same period last year.',
    widget: 'KpiCard',
    load: salesKpi('Sales this year', 'vs last year', (data) => data.yearToDate()),
  },
  {
    id: 'orders-month',
    title: 'Orders this month',
    description: 'Number of sales orders since the 1st of this month.',
    widget: 'KpiCard',
    load: async (data) => {
      const sales = await data.monthToDate()
      return { title: 'Orders this month', measure: 'orders', value: sales.orderCount, caption: 'since the 1st' }
    },
  },
  {
    id: 'month-on-month',
    title: 'Month-on-month sales',
    description: 'Net sales for each of the last 12 months.',
    widget: 'BarChart',
    load: async (data) => ({
      title: 'Month-on-month sales',
      measure: 'sales',
      valueFormat: 'currency',
      data: (await data.monthOnMonth(12)).map((month) => ({ label: monthNames[month.month - 1], value: month.netAmount })),
    }),
  },
  {
    id: 'day-sales',
    title: 'Day sales',
    description: 'Net sales for each day of this month, with last month behind it.',
    widget: 'LineChart',
    load: async (data) => {
      const { thisMonth, lastMonth } = await data.daySales()
      const point = (day: { day: number; netAmount: number }) => ({ label: String(day.day), value: day.netAmount })
      return {
        title: 'Day sales',
        measure: 'sales',
        valueFormat: 'currency',
        data: thisMonth.map(point),
        compare: lastMonth.map(point),
        label: 'This month',
        compareLabel: 'Last month',
      }
    },
  },
  {
    id: 'high-value-sales',
    title: 'Recent high-value sales',
    description: 'The latest sales orders above the high-value limit.',
    widget: 'DataTable',
    load: async (data) => ({
      title: 'Recent high-value sales',
      columns: [
        { key: 'order', label: 'Order' },
        { key: 'customer', label: 'Customer' },
        { key: 'status', label: 'Status', format: 'status' },
        { key: 'amount', label: 'Amount', format: 'currency' },
      ],
      rows: (await data.highValueOrders(5)).map((order) => ({ order: order.order, customer: order.customerName, status: order.status, amount: order.netAmount })),
    }),
  },
  {
    id: 'top-customers',
    title: 'Top customers',
    description: 'Customers ranked by net sales this month.',
    widget: 'RankedList',
    load: async (data) => ({
      title: 'Top customers',
      measure: 'sales',
      valueFormat: 'currency',
      items: (await data.topCustomers(5)).map((customer) => ({ label: customer.name, value: customer.netAmount })),
    }),
  },
  {
    id: 'top-materials',
    title: 'Top materials',
    description: 'Materials ranked by net sales this month.',
    widget: 'RankedList',
    load: async (data) => ({
      title: 'Top materials',
      measure: 'sales',
      valueFormat: 'currency',
      items: (await data.topMaterials(5)).map((material) => ({ label: material.description, value: material.netAmount })),
    }),
  },
  {
    id: 'status-split',
    title: 'Invoice status split',
    description: 'Share of orders that are paid, open or overdue.',
    widget: 'DonutChart',
    load: async (data) => ({
      title: 'Invoice status',
      measure: 'orders',
      slices: (await data.statusSplit()).map((share) => ({
        label: share.status,
        value: share.orders,
        tone: share.status === 'Paid' ? 'positive' : share.status === 'Overdue' ? 'negative' : undefined,
      })),
    }),
  },
]
