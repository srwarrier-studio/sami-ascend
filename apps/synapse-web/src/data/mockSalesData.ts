import type { DaySales, MonthSales, SalesData } from './salesData'

const customers = [
  ['0000100001', 'Northwind Trading', 412000],
  ['0000100002', 'Harbor Steel Works', 368000],
  ['0000100003', 'Alder Construction', 301000],
  ['0000100004', 'Kestrel Logistics', 244000],
  ['0000100005', 'Meridian Foods', 197000],
] as const

const materials = [
  ['MAT-1001', 'Rebar 12mm', 520000],
  ['MAT-1002', 'Cement 42.5R', 448000],
  ['MAT-1003', 'Steel plate 8mm', 371000],
  ['MAT-1004', 'PVC conduit', 255000],
  ['MAT-1005', 'Copper wire', 213000],
] as const

const orders = [
  ['0000012030', 'Northwind Trading', 84200, 'Paid'],
  ['0000012029', 'Harbor Steel Works', 71950, 'Open'],
  ['0000012028', 'Alder Construction', 66300, 'Overdue'],
  ['0000012027', 'Kestrel Logistics', 58780, 'Paid'],
  ['0000012026', 'Meridian Foods', 52415, 'Open'],
] as const

export class MockSalesData implements SalesData {
  private readonly now: Date

  constructor(now: Date = new Date()) {
    this.now = now
  }

  async today() {
    return { netAmount: 125000, previousNetAmount: 118000, orderCount: 14, trend: [98000, 110000, 104000, 118000, 125000] }
  }

  async monthToDate() {
    return { netAmount: 3400000, previousNetAmount: 3200000, orderCount: 312, trend: [2.1, 2.3, 2.2, 2.6, 2.8, 2.7, 3.0, 3.4].map((v) => v * 1000000) }
  }

  async yearToDate() {
    return { netAmount: 29800000, previousNetAmount: 27100000, orderCount: 2890, trend: [4, 8, 12, 15, 19, 23, 26, 29.8].map((v) => v * 1000000) }
  }

  async monthOnMonth(months: number): Promise<MonthSales[]> {
    return Array.from({ length: months }, (_, index) => {
      const date = new Date(Date.UTC(this.now.getUTCFullYear(), this.now.getUTCMonth() - (months - 1 - index), 1))
      return { year: date.getUTCFullYear(), month: date.getUTCMonth() + 1, netAmount: Math.round(2000000 + index * 120000 + ((index * 7) % 5) * 60000) }
    })
  }

  async daySales() {
    const series = (offset: number): DaySales[] =>
      Array.from({ length: 28 }, (_, index) => ({ day: index + 1, netAmount: Math.round(1400000 + index * 25000 + Math.sin(index * 0.9 + offset) * 300000) }))
    return { thisMonth: series(0), lastMonth: series(1) }
  }

  async topCustomers(top: number) {
    return customers.slice(0, top).map(([customer, name, netAmount]) => ({ customer, name, netAmount }))
  }

  async topMaterials(top: number) {
    return materials.slice(0, top).map(([material, description, netAmount]) => ({ material, description, netAmount }))
  }

  async highValueOrders(top: number) {
    const date = this.now.toISOString().slice(0, 10)
    return orders.slice(0, top).map(([order, customerName, netAmount, status]) => ({ order, customerName, orderDate: date, netAmount, status }))
  }

  async statusSplit() {
    return [
      { status: 'Paid', orders: 58 },
      { status: 'Open', orders: 27 },
      { status: 'Overdue', orders: 15 },
    ]
  }
}
