import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, synapsePalette } from '@sami/ui'
import App from '../src/App'
import { MockBoardStore } from '../src/boards/boardStore'
import { MockCatalogClient } from '../src/catalog/mockCatalogClient'
import { MockSessionClient } from '../src/session/sessionClient'

const boards = (count: number) =>
  Array.from({ length: count }, (_, index) => ({ id: `b${index + 1}`, name: `Board ${index + 1}`, widgets: [{ id: `w${index + 1}`, catalogId: 'sales-today' }] }))

const open = (count: number) => {
  const store = new MockBoardStore(boards(count))
  render(
    <UiProvider palette={synapsePalette}>
      <App client={new MockSessionClient('manager@mock-sami.com')} catalogClient={new MockCatalogClient()} boardStore={store} history={createMemoryHistory({ initialEntries: ['/'] })} />
    </UiProvider>,
  )
  return store
}

const showPresets = async () => {
  await userEvent.click(await screen.findByRole('button', { name: 'Add widget' }))
  await userEvent.click(await screen.findByText('Preset boards'))
}

describe('the preset boards tab', () => {
  it('keeps the widget library on the first tab', async () => {
    open(1)
    await userEvent.click(await screen.findByRole('button', { name: 'Add widget' }))
    expect(await screen.findByLabelText('Search widgets')).toBeInTheDocument()
  })

  it('lists each preset with its description and widget count', async () => {
    open(1)
    await showPresets()
    expect(screen.getByText('Customers and materials')).toBeInTheDocument()
    expect(screen.getByText('Who buys, what sells and the biggest sales.')).toBeInTheDocument()
    expect(screen.getAllByText('2 widgets').length).toBeGreaterThan(0)
  })
})

describe('using a preset', () => {
  it('creates a board with the preset name, opens it and closes the drawer', async () => {
    const store = open(1)
    await showPresets()
    await userEvent.click(screen.getByRole('button', { name: 'Use Customers and materials' }))
    await userEvent.click(await screen.findByRole('button', { name: 'Save' }))
    expect(await screen.findByRole('heading', { name: 'Customers and materials' })).toBeInTheDocument()
    await waitFor(() => expect(screen.queryByLabelText('Search widgets')).not.toBeInTheDocument())
    const created = (await store.list()).find((board) => board.name === 'Customers and materials')
    expect(created?.widgets.map((widget) => widget.catalogId)).toEqual(['top-customers', 'top-materials'])
  })

  it('leaves the board the user was on unchanged', async () => {
    const store = open(1)
    await showPresets()
    await userEvent.click(screen.getByRole('button', { name: 'Use Daily pulse' }))
    await userEvent.click(await screen.findByRole('button', { name: 'Save' }))
    await screen.findByRole('heading', { name: 'Daily pulse' })
    expect((await store.list())[0].widgets.map((widget) => widget.catalogId)).toEqual(['sales-today'])
  })

  it('at 3 boards asks which to replace and changes nothing until confirmed', async () => {
    const store = open(3)
    await showPresets()
    await userEvent.click(screen.getByRole('button', { name: 'Use Daily pulse' }))
    const dialog = await screen.findByRole('dialog', { name: 'Save as board' })
    expect(within(dialog).getByRole('button', { name: /Replace/ })).toBeDisabled()
    await userEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }))
    expect((await store.list()).map((board) => board.name)).toEqual(['Board 1', 'Board 2', 'Board 3'])
  })

  it('at 3 boards replaces the chosen board once confirmed', async () => {
    const store = open(3)
    await showPresets()
    await userEvent.click(screen.getByRole('button', { name: 'Use Daily pulse' }))
    const dialog = await screen.findByRole('dialog', { name: 'Save as board' })
    await userEvent.click(within(dialog).getByLabelText('Board 2'))
    await userEvent.click(within(dialog).getByRole('button', { name: 'Replace Board 2' }))
    expect(await screen.findByRole('heading', { name: 'Daily pulse' })).toBeInTheDocument()
    expect((await store.list()).map((board) => board.name)).toEqual(['Board 1', 'Daily pulse', 'Board 3'])
  })
})
