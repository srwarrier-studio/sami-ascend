import { useState } from 'react'
import {
  Accordion,
  ActionIcon,
  Alert,
  Avatar,
  Badge,
  BarChart,
  Breadcrumbs,
  Button,
  Card,
  Checkbox,
  Divider,
  Drawer,
  Group,
  LineChart,
  Loader,
  Menu,
  Modal,
  MultiSelect,
  NavLink,
  NumberInput,
  Pagination,
  PasswordInput,
  Progress,
  Radio,
  registry,
  SegmentedControl,
  Select,
  SimpleGrid,
  Skeleton,
  Stack,
  Switch,
  Table,
  Tabs,
  Text,
  Textarea,
  TextInput,
  Title,
  Tooltip,
  notifications,
} from '../src'
import { TokensSection } from './TokensSection'

const days = [
  { label: 'Mon', value: 120000 },
  { label: 'Tue', value: 180000 },
  { label: 'Wed', value: 150000 },
  { label: 'Thu', value: 210000 },
]

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card>
      <Stack>
        <Title order={4}>{title}</Title>
        {children}
      </Stack>
    </Card>
  )
}

const toasts = [
  { label: 'Success', color: 'green', title: 'Order created', message: 'Sales order 0000012031 was saved' },
  { label: 'Error', color: 'red', title: 'SAP unavailable', message: 'Try again in a few minutes' },
  { label: 'Warning', color: 'yellow', title: 'Credit limit', message: 'Customer is close to the limit' },
  { label: 'Info', color: 'blue', title: 'Refreshed', message: 'Dashboard data is up to date' },
]

export function KitchenSink() {
  const [modal, setModal] = useState(false)
  const [drawer, setDrawer] = useState(false)
  const [page, setPage] = useState(1)

  return (
    <Stack>
      <TokensSection />

      <Section title="Buttons">
        <Group>
          <Button>Primary</Button>
          <Button variant="light">Light</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="default">Default</Button>
          <Button variant="subtle">Subtle</Button>
          <Button color="red">Danger</Button>
          <Button loading>Loading</Button>
          <Button disabled>Disabled</Button>
          <Button size="xs">Small</Button>
          <Button size="lg">Large</Button>
          <ActionIcon aria-label="Action">
            <Loader size="xs" />
          </ActionIcon>
        </Group>
      </Section>

      <Section title="Inputs">
        <SimpleGrid cols={3}>
          <TextInput label="Text" placeholder="name" description="Helper text" />
          <TextInput label="With error" error="Required" />
          <PasswordInput label="Password" />
          <NumberInput label="Quantity" defaultValue={1} min={0} />
          <Select label="Plant" data={['1000', '2000', '3000']} placeholder="Pick one" />
          <MultiSelect label="Materials" data={['TG11', 'TG12', 'TG13']} placeholder="Pick several" />
          <TextInput label="Date" type="date" />
          <Textarea label="Notes" rows={2} />
          <TextInput label="Disabled" disabled value="Locked" />
        </SimpleGrid>
        <Group>
          <Checkbox label="Checkbox" defaultChecked />
          <Switch label="Switch" defaultChecked />
          <Radio.Group defaultValue="a">
            <Group>
              <Radio value="a" label="Radio A" />
              <Radio value="b" label="Radio B" />
            </Group>
          </Radio.Group>
          <SegmentedControl data={['Day', 'Month', 'Year']} />
        </Group>
      </Section>

      <Section title="Data display">
        <Group>
          <Avatar color="brand">SA</Avatar>
          <Avatar color="brand" variant="filled">MS</Avatar>
        </Group>
        <Divider />
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Order</Table.Th>
              <Table.Th>Customer</Table.Th>
              <Table.Th>Status</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            <Table.Tr>
              <Table.Td>0000012031</Table.Td>
              <Table.Td>0000100001</Table.Td>
              <Table.Td><Badge color="green">Delivered</Badge></Table.Td>
            </Table.Tr>
            <Table.Tr>
              <Table.Td>0000012032</Table.Td>
              <Table.Td>0000100002</Table.Td>
              <Table.Td><Badge>Open</Badge></Table.Td>
            </Table.Tr>
          </Table.Tbody>
        </Table>
      </Section>

      <Section title="Overlays">
        <Group>
          <Button variant="default" onClick={() => setModal(true)}>Open modal</Button>
          <Button variant="default" onClick={() => setDrawer(true)}>Open drawer</Button>
          <Menu>
            <Menu.Target>
              <Button variant="default">Menu</Button>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Label>Order</Menu.Label>
              <Menu.Item>Edit</Menu.Item>
              <Menu.Item>Copy</Menu.Item>
              <Menu.Divider />
              <Menu.Item color="red">Delete</Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
        <Modal opened={modal} onClose={() => setModal(false)} title="Confirm">
          <Text>Create this sales order?</Text>
          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={() => setModal(false)}>Cancel</Button>
            <Button onClick={() => setModal(false)}>Create</Button>
          </Group>
        </Modal>
        <Drawer opened={drawer} onClose={() => setDrawer(false)} title="Order details" position="right">
          <Text>Drawer content</Text>
        </Drawer>
      </Section>

      <Section title="Feedback">
        <Stack>
          <Alert title="Info" color="blue">Incorrect username or password</Alert>
          <Alert title="Success" color="green">Order saved</Alert>
          <Alert title="Warning" color="yellow">Credit limit almost reached</Alert>
          <Alert title="Error" color="red">SAP is not reachable</Alert>
        </Stack>
        <Group>
          <Badge>Open</Badge>
          <Badge color="green">Delivered</Badge>
          <Badge color="red" variant="outline">Blocked</Badge>
          <Loader />
          <Tooltip label="Tooltip text">
            <Button variant="default">Hover me</Button>
          </Tooltip>
        </Group>
        <Progress value={60} />
        <Group>
          <Skeleton height="2rem" width="10rem" />
          <Skeleton height="2rem" width="6rem" />
        </Group>
      </Section>

      <Section title="Notifications">
        <Group>
          {toasts.map((toast) => (
            <Button
              key={toast.label}
              variant="light"
              color={toast.color}
              onClick={() => notifications.show({ title: toast.title, message: toast.message, color: toast.color })}
            >
              {toast.label}
            </Button>
          ))}
          <Button
            variant="default"
            onClick={() => {
              const id = notifications.show({ title: 'Saving', message: 'Posting to SAP', loading: true, autoClose: false })
              setTimeout(
                () => notifications.update({ id, title: 'Saved', message: 'Posted to SAP', loading: false, color: 'green', autoClose: 3000 }),
                1500,
              )
            }}
          >
            Loading then done
          </Button>
          <Button variant="default" onClick={() => notifications.clean()}>
            Clear all
          </Button>
        </Group>
      </Section>

      <Section title="Navigation">
        <Tabs defaultValue="items">
          <Tabs.List>
            <Tabs.Tab value="items">Items</Tabs.Tab>
            <Tabs.Tab value="partners">Partners</Tabs.Tab>
            <Tabs.Tab value="texts">Texts</Tabs.Tab>
          </Tabs.List>
          <Tabs.Panel value="items" pt="md">Items panel</Tabs.Panel>
          <Tabs.Panel value="partners" pt="md">Partners panel</Tabs.Panel>
          <Tabs.Panel value="texts" pt="md">Texts panel</Tabs.Panel>
        </Tabs>
        <Breadcrumbs>
          <Text>Sales orders</Text>
          <Text>New</Text>
        </Breadcrumbs>
        <Group>
          <NavLink label="Sales orders" active w="12rem" />
          <NavLink label="Reports" w="12rem" />
        </Group>
        <Pagination total={10} value={page} onChange={setPage} />
        <Accordion defaultValue="a">
          <Accordion.Item value="a">
            <Accordion.Control>Accordion item</Accordion.Control>
            <Accordion.Panel>Panel content</Accordion.Panel>
          </Accordion.Item>
          <Accordion.Item value="b">
            <Accordion.Control>Another item</Accordion.Control>
            <Accordion.Panel>More content</Accordion.Panel>
          </Accordion.Item>
        </Accordion>
      </Section>

      <Section title="Widgets and charts">
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
      </Section>
    </Stack>
  )
}
