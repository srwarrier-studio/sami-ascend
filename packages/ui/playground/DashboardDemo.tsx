import {
  AreaChart,
  BarChart,
  Button,
  DataTable,
  DonutChart,
  GaugeChart,
  HeatmapChart,
  Divider,
  Group,
  KpiCard,
  LineChart,
  PageHeader,
  PencilSimpleIcon,
  PlusIcon,
  RankedList,
  SimpleGrid,
  SparkleIcon,
  Stack,
  StackedBarChart,
} from '../src'

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

export function DashboardDemo() {
  return (
    <>
      <PageHeader
        title="Sales overview"
        breadcrumb={['Boards', 'Sales overview']}
        actions={
          <Group>
            <Button variant="default" leftSection={<PencilSimpleIcon size={16} />}>
              Edit
            </Button>
            <Button variant="light" leftSection={<SparkleIcon size={16} weight="fill" />}>
              AI Mode
            </Button>
            <Button leftSection={<PlusIcon size={16} />}>Add widget</Button>
          </Group>
        }
      />
      <Stack p="md">
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }}>
          <KpiCard title="Sales this month" value={3400000} valueFormat="currency" delta={0.062} caption="vs last month" trend={[2.1, 2.3, 2.2, 2.6, 2.8, 2.7, 3.0, 3.4]} />
          <KpiCard title="Invoices" value={1284} delta={0.031} caption="Raised this month" trend={[1100, 1150, 1120, 1210, 1180, 1250, 1284]} />
          <KpiCard title="Active customers" value={312} caption="9 new this month" trend={[290, 296, 301, 303, 308, 312]} />
          <KpiCard title="Average invoice" value={2648} valueFormat="currency" delta={-0.014} caption="vs last month" trend={[2750, 2700, 2720, 2680, 2660, 2648]} />
        </SimpleGrid>
        <SimpleGrid cols={{ base: 1, lg: 2 }}>
          <LineChart title="Day sales" data={days} compare={lastMonth} label="This month" compareLabel="Last month" valueFormat="currency" />
          <BarChart title="Month-on-month sales" data={months} valueFormat="currency" />
        </SimpleGrid>
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }}>
          <DonutChart
            title="Invoice status"
            slices={[
              { label: 'Paid', value: 58, tone: 'positive' },
              { label: 'Open', value: 27 },
              { label: 'Overdue', value: 15, tone: 'negative' },
            ]}
          />
          <GaugeChart title="Month target" value={3400000} target={5000000} valueFormat="currency" caption="this month" />
          <AreaChart title="Cumulative sales" data={cumulative} valueFormat="currency" />
        </SimpleGrid>
        <SimpleGrid cols={{ base: 1, lg: 2 }}>
          <StackedBarChart title="Sales by invoice status" series={byStatus} valueFormat="currency" />
          <HeatmapChart title="Orders by weekday and hour" cells={busy} />
        </SimpleGrid>
        <SimpleGrid cols={{ base: 1, lg: 3 }}>
          <RankedList title="Top customers" items={customers} valueFormat="currency" />
          <RankedList title="Top materials" items={materials} valueFormat="currency" />
          <DataTable
            title="Recent high-value sales"
            columns={[
              { key: 'invoice', label: 'Invoice', format: 'text' },
              { key: 'customer', label: 'Customer', format: 'text' },
              { key: 'status', label: 'Status', format: 'text' },
              { key: 'amount', label: 'Amount', format: 'currency' },
            ]}
            rows={sales}
          />
        </SimpleGrid>
        <Divider />
        <Group gap="xs" aria-label="Board pages" role="group">
          <Button variant="light" size="xs">
            Page 1
          </Button>
          <Button variant="subtle" color="gray" size="xs">
            Page 2
          </Button>
          <Button variant="subtle" size="xs" leftSection={<PlusIcon size={14} />}>
            Add
          </Button>
        </Group>
      </Stack>
    </>
  )
}
