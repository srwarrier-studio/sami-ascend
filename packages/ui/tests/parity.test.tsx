import { fireEvent, render, screen, within } from '@testing-library/react'
import { useState } from 'react'
import { Alert, PageBar, PageHeader, SignInCard, SplashScreen, UiProvider, WidgetCatalog, registry, synapsePalette } from '../src'
import type { PageBarConfig } from '../src'

const wrap = (node: React.ReactNode) => render(<UiProvider palette={synapsePalette}>{node}</UiProvider>)

describe('soft header and alerts', () => {
  it('shows the title and breadcrumb', () => {
    wrap(<PageHeader title="Sales" breadcrumb={['Boards']} />)
    expect(screen.getByRole('heading', { name: 'Sales' })).toBeInTheDocument()
  })

  it.each(['blue', 'green', 'yellow', 'red'])('renders a %s alert with an icon', (color) => {
    const { container } = wrap(<Alert color={color}>Message</Alert>)
    expect(container.querySelector('svg')).not.toBeNull()
  })
})

describe('launch screens', () => {
  it('splash shows name and tagline', () => {
    wrap(<SplashScreen name="Synapse" tagline="Your sales" />)
    expect(screen.getByText('Synapse')).toBeInTheDocument()
    expect(screen.getByText('Your sales')).toBeInTheDocument()
  })

  it('sign in submits email and password and shows the error', () => {
    const onSubmit = vi.fn()
    wrap(<SignInCard title="Sign in" error="Wrong password" onSubmit={onSubmit} />)
    fireEvent.change(screen.getByLabelText(/Work email/), { target: { value: 'a@b.com' } })
    fireEvent.change(screen.getByLabelText(/Password/), { target: { value: 'secret' } })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(onSubmit).toHaveBeenCalledWith('a@b.com', 'secret')
    expect(screen.getByText('Wrong password')).toBeInTheDocument()
  })
})

describe('widget catalog', () => {
  it('has one row per registry widget and reports the pick', () => {
    const onPick = vi.fn()
    wrap(<WidgetCatalog onPick={onPick} />)
    expect(screen.getAllByRole('button', { name: /^Add / })).toHaveLength(registry.names().length)
    fireEvent.click(screen.getByRole('button', { name: 'Add KpiCard' }))
    expect(onPick).toHaveBeenCalledWith('KpiCard')
  })
})

const config: PageBarConfig = { palette: 'teal', scheme: 'light', motion: 'full' }

function Bar({ editing, onConfig = () => undefined }: { editing: boolean; onConfig?: (config: PageBarConfig) => void }) {
  const [tabs, setTabs] = useState([
    { id: 'a', name: 'Alpha' },
    { id: 'b', name: 'Beta' },
    { id: 'c', name: 'Gamma' },
    { id: 'd', name: 'Delta' },
  ])
  const [active, setActive] = useState('a')
  return (
    <PageBar
      tabs={tabs}
      activeId={active}
      editing={editing}
      config={config}
      onSelect={setActive}
      onAdd={() => setTabs([...tabs, { id: 'e', name: 'Epsilon' }])}
      onRename={(id, name) => setTabs(tabs.map((tab) => (tab.id === id ? { ...tab, name } : tab)))}
      onConfigChange={onConfig}
    />
  )
}

describe('page bar', () => {
  it('lists every tab in one scroll container and selects on click', () => {
    wrap(<Bar editing={false} />)
    const tabs = within(screen.getByRole('tablist')).getAllByRole('tab')
    expect(tabs).toHaveLength(4)
    fireEvent.click(screen.getByRole('tab', { name: 'Gamma' }))
    expect(screen.getByRole('tab', { name: 'Gamma' })).toHaveAttribute('aria-selected', 'true')
  })

  it('adds a board', () => {
    wrap(<Bar editing={false} />)
    fireEvent.click(screen.getByRole('button', { name: 'Add' }))
    expect(screen.getByRole('tab', { name: 'Epsilon' })).toBeInTheDocument()
  })

  it('cannot rename outside Edit mode', () => {
    wrap(<Bar editing={false} />)
    expect(screen.queryByRole('button', { name: 'Rename Alpha' })).toBeNull()
    fireEvent.doubleClick(screen.getByRole('tab', { name: 'Alpha' }))
    expect(screen.queryByRole('textbox')).toBeNull()
  })

  it('renames in Edit mode with Enter and ignores an empty name', () => {
    wrap(<Bar editing />)
    fireEvent.click(screen.getByRole('button', { name: 'Rename Alpha' }))
    fireEvent.change(screen.getByRole('textbox', { name: 'Rename Alpha' }), { target: { value: 'Sales' } })
    fireEvent.keyDown(screen.getByRole('textbox', { name: 'Rename Alpha' }), { key: 'Enter' })
    expect(screen.getByRole('tab', { name: 'Sales' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Rename Sales' }))
    fireEvent.change(screen.getByRole('textbox', { name: 'Rename Sales' }), { target: { value: '  ' } })
    fireEvent.keyDown(screen.getByRole('textbox', { name: 'Rename Sales' }), { key: 'Enter' })
    expect(screen.getByRole('tab', { name: 'Sales' })).toBeInTheDocument()
  })

  it('escape cancels a rename', () => {
    wrap(<Bar editing />)
    fireEvent.click(screen.getByRole('button', { name: 'Rename Beta' }))
    fireEvent.change(screen.getByRole('textbox', { name: 'Rename Beta' }), { target: { value: 'Nope' } })
    fireEvent.keyDown(screen.getByRole('textbox', { name: 'Rename Beta' }), { key: 'Escape' })
    expect(screen.getByRole('tab', { name: 'Beta' })).toBeInTheDocument()
  })

  it('reports quick config changes', async () => {
    const onConfig = vi.fn()
    wrap(<Bar editing={false} onConfig={onConfig} />)
    fireEvent.click(screen.getByRole('button', { name: 'Quick settings' }))
    fireEvent.click(await screen.findByText('Dark'))
    expect(onConfig).toHaveBeenCalledWith({ ...config, scheme: 'dark' })
    fireEvent.click(screen.getByText('Minimal'))
    expect(onConfig).toHaveBeenCalledWith({ ...config, motion: 'minimal' })
    fireEvent.click(screen.getByText('Copper'))
    expect(onConfig).toHaveBeenCalledWith({ ...config, palette: 'copper' })
  })
})
