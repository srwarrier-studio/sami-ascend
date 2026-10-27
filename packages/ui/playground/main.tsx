import { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { KitchenSink } from './KitchenSink'
import {
  AppFrame,
  Button,
  Card,
  ClipboardTextIcon,
  Container,
  FileTextIcon,
  FilesIcon,
  Group,
  PageHeader,
  SquaresFourIcon,
  Stack,
  TextInput,
  UiProvider,
  UsersIcon,
  workspacePalette,
} from '../src'

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
          <KitchenSink />
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
