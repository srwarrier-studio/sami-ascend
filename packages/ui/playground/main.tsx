import { useState } from 'react'
import { createRoot } from 'react-dom/client'
import {
  Alert,
  AppFrame,
  ClipboardTextIcon,
  FileTextIcon,
  FilesIcon,
  PageHeader,
  SquaresFourIcon,
  UsersIcon,
  BarChart,
  Button,
  Card,
  Container,
  Group,
  Loader,
  LineChart,
  NavLink,
  PasswordInput,
  registry,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
  Title,
  UiProvider,
  workspacePalette,
} from '../src'
import type { Palette } from '../src'

const days = [
  { label: 'Mon', value: 120000 },
  { label: 'Tue', value: 180000 },
  { label: 'Wed', value: 150000 },
  { label: 'Thu', value: 210000 },
]

function Gallery({ name, palette }: { name: string; palette: Palette }) {
  return (
    <UiProvider palette={palette}>
      <Container>
        <Stack>
          <Title order={2}>{name}</Title>
          <Group>
            <Button>Primary</Button>
            <Button variant="light">Light</Button>
            <Button variant="outline">Outline</Button>
            <Loader />
          </Group>
          <TextInput label="Username" placeholder="name" />
          <PasswordInput label="Password" />
          <Alert title="Heads up">Incorrect username or password</Alert>
          <Card>
            <Title order={4}>Card</Title>
            <Text>Body text</Text>
            <NavLink label="Sales orders" active />
            <NavLink label="Reports" />
          </Card>
          <SimpleGrid cols={3}>
            {registry.render('KpiCard', { title: 'Today', value: 125000, valueFormat: 'currency', delta: 0.05, caption: 'vs yesterday' })}
            {registry.render('RankedList', { title: 'Top customers', items: days, valueFormat: 'currency' })}
            {registry.render('DataTable', {
              title: 'Recent high-value sales',
              columns: [
                { key: 'order', label: 'Order' },
                { key: 'amount', label: 'Amount', format: 'currency' },
              ],
              rows: [{ order: '0000012031', amount: 500000 }],
            })}
          </SimpleGrid>
          <SimpleGrid cols={2}>
            <LineChart data={days} title="Day sales" valueFormat="currency" />
            <BarChart data={days} title="Top customers" valueFormat="currency" />
          </SimpleGrid>
        </Stack>
      </Container>
    </UiProvider>
  )
}

function Demo() {
  const [page, setPage] = useState('orders')
  const link = (key: string) => ({ onSelect: () => setPage(key) })
  return (
    <UiProvider palette={workspacePalette}>
      <AppFrame
        brand={{ name: 'Workspace', subtitle: 'Sales' }}
        user={{ name: 'Mock Sami Admin', email: 'admin@mock-sami.com' }}
        onSignOut={() => undefined}
        notifications={3}
        searchPlaceholder="Search orders or customers"
        navGroups={[
          [{ key: 'tasks', label: 'Tasks', icon: ClipboardTextIcon, badge: 2, ...link('tasks'), active: page === 'tasks' }],
          [
            { key: 'dashboard', label: 'Dashboard', icon: SquaresFourIcon, ...link('dashboard'), active: page === 'dashboard' },
            { key: 'orders', label: 'Sales orders', icon: FileTextIcon, ...link('orders'), active: page === 'orders' },
            { key: 'documents', label: 'Documents', icon: FilesIcon, ...link('documents'), active: page === 'documents' },
            { key: 'kitchen', label: 'Kitchen sink', icon: UsersIcon, ...link('kitchen'), active: page === 'kitchen' },
          ],
        ]}
      >
        {page === 'kitchen' ? (
          <Gallery name="Workspace" palette={workspacePalette} />
        ) : (
          <>
            <PageHeader
              title="New sales order"
              breadcrumb={['Sales orders', 'New']}
              actions={
                <Group>
                  <Button variant="default">Cancel</Button>
                  <Button>Create order</Button>
                </Group>
              }
            />
            <Container py="md">
              <Card>
                <Stack>
                  <TextInput label="Customer" placeholder="0000100001" />
                  <TextInput label="Delivery date" type="date" />
                </Stack>
              </Card>
            </Container>
          </>
        )}
      </AppFrame>
    </UiProvider>
  )
}

createRoot(document.getElementById('root')!).render(<Demo />)
