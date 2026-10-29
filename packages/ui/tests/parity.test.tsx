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

function Bar({ onConfig = () => undefined }: { onConfig?: (config: PageBarConfig) => void }) {
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
      config={config}
      onSelect={setActive}
      onAdd={() => setTabs([...tabs, { id: 'e', name: 'Epsilon' }])}
      onConfigChange={onConfig}
    />
  )
}

describe('page header title', () => {
  const header = (editing: boolean, onTitleChange = vi.fn()) => {
    wrap(<PageHeader title="Sales" editing={editing} onTitleChange={onTitleChange} />)
    return onTitleChange
  }

  it('is plain text outside Edit mode', () => {
    header(false)
    expect(screen.queryByRole('textbox')).toBeNull()
  })

  it('saves a new title on Enter', () => {
    const onTitleChange = header(true)
    const input = screen.getByRole('textbox', { name: 'Board title' })
    fireEvent.change(input, { target: { value: 'Revenue' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    fireEvent.blur(input)
    expect(onTitleChange).toHaveBeenCalledWith('Revenue')
  })

  it('ignores an empty title', () => {
    const onTitleChange = header(true)
    const input = screen.getByRole('textbox', { name: 'Board title' })
    fireEvent.change(input, { target: { value: '  ' } })
    fireEvent.blur(input)
    expect(onTitleChange).not.toHaveBeenCalled()
    expect(input).toHaveValue('Sales')
  })

  it('escape cancels', () => {
    const onTitleChange = header(true)
    const input = screen.getByRole('textbox', { name: 'Board title' })
    fireEvent.change(input, { target: { value: 'Nope' } })
    fireEvent.keyDown(input, { key: 'Escape' })
    fireEvent.blur(input)
    expect(onTitleChange).not.toHaveBeenCalled()
  })
})

describe('page bar', () => {
  it('lists every tab in one scroll container and selects on click', () => {
    wrap(<Bar />)
    expect(within(screen.getByRole('tablist')).getAllByRole('tab')).toHaveLength(4)
    fireEvent.click(screen.getByRole('tab', { name: 'Gamma' }))
    expect(screen.getByRole('tab', { name: 'Gamma' })).toHaveAttribute('aria-selected', 'true')
  })

  it('adds a board', () => {
    wrap(<Bar />)
    fireEvent.click(screen.getByRole('button', { name: 'Add' }))
    expect(screen.getByRole('tab', { name: 'Epsilon' })).toBeInTheDocument()
  })

  it('reports quick config changes', async () => {
    const onConfig = vi.fn()
    wrap(<Bar onConfig={onConfig} />)
    fireEvent.click(screen.getByRole('button', { name: 'Quick settings' }))
    fireEvent.click(await screen.findByText('Dark'))
    expect(onConfig).toHaveBeenCalledWith({ ...config, scheme: 'dark' })
    fireEvent.click(screen.getByText('Minimal'))
    expect(onConfig).toHaveBeenCalledWith({ ...config, motion: 'minimal' })
    fireEvent.click(screen.getByText('Copper'))
    expect(onConfig).toHaveBeenCalledWith({ ...config, palette: 'copper' })
  })
})
