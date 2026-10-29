export type PeriodSales = { netAmount: number; previousNetAmount: number; orderCount: number; trend: number[] }
export type MonthSales = { year: number; month: number; netAmount: number }
export type DaySales = { day: number; netAmount: number }
export type RankedCustomer = { customer: string; name: string; netAmount: number }
export type RankedMaterial = { material: string; description: string; netAmount: number }
export type HighValueOrder = { order: string; customerName: string; orderDate: string; netAmount: number; status: string }
export type StatusShare = { status: string; orders: number }

export type SalesData = {
  today: () => Promise<PeriodSales>
  monthToDate: () => Promise<PeriodSales>
  yearToDate: () => Promise<PeriodSales>
  monthOnMonth: (months: number) => Promise<MonthSales[]>
  daySales: () => Promise<{ thisMonth: DaySales[]; lastMonth: DaySales[] }>
  topCustomers: (top: number) => Promise<RankedCustomer[]>
  topMaterials: (top: number) => Promise<RankedMaterial[]>
  highValueOrders: (top: number) => Promise<HighValueOrder[]>
  statusSplit: () => Promise<StatusShare[]>
}
