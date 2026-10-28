import { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { DashboardDemo } from './DashboardDemo'
import { KitchenSink } from './KitchenSink'
import { ThemeLab, defaultLab } from './ThemeLab'
import {
  AppFrame,
  Button,
  Card,
  Container,
  FileTextIcon,
  FilesIcon,
  Group,
  PageHeader,
  Stack,
  SquaresFourIcon,
  TextInput,
  UiProvider,
  presets,
} from '../src'

function Demo() {
  const [page, setPage] = useState('dashboard')
  const [lab, setLab] = useState(defaultLab)
  const link = (key: string) => ({ onSelect: () => setPage(key), active: page === key })
  return (
    <UiProvider palette={presets[lab.palette]} radius={lab.radius} motion={lab.motion}>
      <AppFrame
        layout={lab.layout}
        brand={{ name: 'Playground', subtitle: '@sami/ui' }}
        user={{ name: 'Mock Sami Admin', email: 'admin@mock-sami.com' }}
        onSignOut={() => undefined}
        notifications={3}
        searchPlaceholder="Search"
        navGroups={[
          [
            { key: 'dashboard', label: 'Dashboard', icon: SquaresFourIcon, ...link('dashboard') },
            { key: 'kitchen', label: 'Kitchen sink', icon: FilesIcon, ...link('kitchen') },
            { key: 'orders', label: 'New sales order', icon: FileTextIcon, ...link('orders') },
          ],
        ]}
      >
        {page === 'dashboard' ? (
          <>
            <Container py="md">
              <ThemeLab lab={lab} onChange={setLab} />
            </Container>
            <DashboardDemo />
          </>
        ) : page === 'kitchen' ? (
          <Container py="md">
            <Stack>
              <ThemeLab lab={lab} onChange={setLab} />
              <KitchenSink />
            </Stack>
          </Container>
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
