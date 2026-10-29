import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, synapsePalette } from '@sami/ui'
import App from '../src/App'
import { CatalogWidget } from '../src/catalog/CatalogWidget'
import { catalog, matchCatalog } from '../src/catalog/catalog'
import { MockBoardStore } from '../src/boards/boardStore'
import { MockSalesData } from '../src/data/mockSalesData'
import { MockSessionClient } from '../src/session/sessionClient'

const data = new MockSalesData(new Date('2026-10-29T10:00:00Z'))

const small = () =>
  new MockBoardStore([
    { id: 'b1', name: 'First', widgets: [{ id: 'w1', catalogId: 'top-customers' }, { id: 'w2', catalogId: 'top-materials' }] },
    { id: 'b2', name: 'Second', widgets: [{ id: 'w3', catalogId: 'sales-today' }] },
  ])

const open = (store = small()) => {
  render(
    <UiProvider palette={synapsePalette}>
      <App client={new MockSessionClient('manager@mock-sami.com')} salesData={data} boardStore={store} history={createMemoryHistory({ initialEntries: ['/'] })} />
    </UiProvider>,
  )
  return store
}

const edit = async () => userEvent.click(await screen.findByRole('button', { name: 'Edit' }))

describe('board page', () => {
  it('shows the first board with its widgets and every board in the bar', async () => {
    open()
    expect(await screen.findByRole('heading', { name: 'First' })).toBeInTheDocument()
    expect(await screen.findByText('Top customers')).toBeInTheDocument()
    expect(within(screen.getByRole('tablist')).getAllByRole('tab').map((tab) => tab.textContent)).toEqual(['First', 'Second'])
  })

  it('switches boards', async () => {
    open()
    await userEvent.click(await screen.findByRole('tab', { name: 'Second' }))
    expect(await screen.findByRole('heading', { name: 'Second' })).toBeInTheDocument()
    expect(await screen.findByText('Sales today')).toBeInTheDocument()
  })

  it('adds a board from the bar', async () => {
    open()
    await userEvent.click(await screen.findByRole('button', { name: 'Add' }))
    expect(await screen.findByRole('heading', { name: 'Board 3' })).toBeInTheDocument()
    expect(screen.getByText(/This board is empty/)).toBeInTheDocument()
  })

  it('has no edit controls outside Edit mode', async () => {
    open()
    await screen.findByRole('heading', { name: 'First' })
    expect(screen.queryByRole('textbox', { name: 'Board title' })).toBeNull()
    expect(screen.queryByRole('button', { name: /^Remove/ })).toBeNull()
    expect(screen.queryByRole('button', { name: 'AI Mode' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Delete board' })).toBeNull()
  })
})

describe('board limit', () => {
  it('allows three boards and notifies on the fourth', async () => {
    const store = open()
    await userEvent.click(await screen.findByRole('button', { name: 'Add' }))
    expect(await screen.findByRole('heading', { name: 'Board 3' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Add' }))
    expect(await screen.findByText('Only 3 sheets allowed')).toBeInTheDocument()
    expect(await store.list()).toHaveLength(3)
  })
})

describe('widget limit', () => {
  const full = () =>
    new MockBoardStore([
      { id: 'b1', name: 'First', widgets: Array.from({ length: 15 }, (_, index) => ({ id: `w${index}`, catalogId: 'sales-today' })) },
    ])

  it('disables the library when the board has 15 widgets', async () => {
    open(full())
    await edit()
    await userEvent.click(await screen.findByRole('button', { name: 'Add widget' }))
    expect(await screen.findByText(/Board is full/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add Day sales' })).toBeDisabled()
  })

  it('adds only what fits from AI Mode', async () => {
    const store = new MockBoardStore([
      { id: 'b1', name: 'First', widgets: Array.from({ length: 14 }, (_, index) => ({ id: `w${index}`, catalogId: 'sales-today' })) },
    ])
    open(store)
    await edit()
    await userEvent.click(await screen.findByRole('button', { name: 'AI Mode' }))
    await userEvent.type(await screen.findByLabelText('What do you want on this board?'), 'sales')
    await userEvent.click(screen.getByRole('button', { name: 'Add widgets' }))
    await waitFor(async () => expect((await store.list())[0].widgets).toHaveLength(15))
  })
})

describe('edit mode', () => {
  it('renames the board in the header and saves it', async () => {
    const store = open()
    await edit()
    const title = await screen.findByRole('textbox', { name: 'Board title' })
    fireEvent.change(title, { target: { value: 'Revenue' } })
    fireEvent.blur(title)
    expect(await screen.findByRole('tab', { name: 'Revenue' })).toBeInTheDocument()
    await waitFor(async () => expect((await store.list())[0].name).toBe('Revenue'))
  })

  it('removes a widget and saves', async () => {
    const store = open()
    await edit()
    await userEvent.click(await screen.findByRole('button', { name: 'Remove Top customers' }))
    expect(screen.queryByRole('button', { name: 'Remove Top customers' })).toBeNull()
    await waitFor(async () => expect((await store.list())[0].widgets.map((w) => w.id)).toEqual(['w2']))
  })

  it('moves a widget later', async () => {
    const store = open()
    await edit()
    await userEvent.click(await screen.findByRole('button', { name: 'Move Top customers later' }))
    await waitFor(async () => expect((await store.list())[0].widgets.map((w) => w.id)).toEqual(['w2', 'w1']))
  })

  it('reorders by dragging one widget onto another', async () => {
    const store = open()
    await edit()
    const first = (await screen.findByRole('button', { name: 'Remove Top customers' })).closest('[draggable]')!
    const second = screen.getByRole('button', { name: 'Remove Top materials' }).closest('[draggable]')!
    fireEvent.dragStart(first)
    await act(() => new Promise((resolve) => setTimeout(resolve)))
    fireEvent.dragEnter(second)
    fireEvent.dragEnd(first)
    await waitFor(async () => expect((await store.list())[0].widgets.map((w) => w.id)).toEqual(['w2', 'w1']))
  })

  it('adds a widget from the catalog', async () => {
    const store = open()
    await edit()
    await userEvent.click(await screen.findByRole('button', { name: 'Add widget' }))
    await userEvent.click(await screen.findByRole('button', { name: 'Add Day sales' }))
    await waitFor(async () => expect((await store.list())[0].widgets.map((w) => w.catalogId)).toEqual(['top-customers', 'top-materials', 'day-sales']))
  })

  it('removes a widget already on the board from the library and cannot add it twice', async () => {
    const store = open()
    await edit()
    await userEvent.click(await screen.findByRole('button', { name: 'Add widget' }))
    await userEvent.click(await screen.findByRole('button', { name: 'Add Day sales' }))
    await userEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Remove Day sales' }))
    await waitFor(async () => expect((await store.list())[0].widgets.map((w) => w.catalogId)).toEqual(['top-customers', 'top-materials']))
    expect(screen.getAllByRole('button', { name: 'Remove Top customers' })[0]).toBeInTheDocument()
  })

  it('AI Mode adds widgets that match the sentence', async () => {
    const store = open()
    await edit()
    await userEvent.click(await screen.findByRole('button', { name: 'AI Mode' }))
    await userEvent.type(await screen.findByLabelText('What do you want on this board?'), 'show me orders')
    await userEvent.click(screen.getByRole('button', { name: 'Add widgets' }))
    expect(await screen.findByText(/Added:/)).toBeInTheDocument()
    await waitFor(async () => expect((await store.list())[0].widgets.some((w) => w.catalogId === 'orders-month')).toBe(true))
  })

  it('AI Mode says when nothing matches', async () => {
    const store = open()
    await edit()
    await userEvent.click(await screen.findByRole('button', { name: 'AI Mode' }))
    await userEvent.type(await screen.findByLabelText('What do you want on this board?'), 'zebra')
    await userEvent.click(screen.getByRole('button', { name: 'Add widgets' }))
    expect(await screen.findByText(/No widget matches/)).toBeInTheDocument()
    expect((await store.list())[0].widgets).toHaveLength(2)
  })

  it('asks before deleting a board, then deletes it', async () => {
    const store = open()
    await edit()
    await userEvent.click(await screen.findByRole('button', { name: 'Delete board' }))
    expect(await screen.findByText('Delete First and its widgets?')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Delete' }))
    expect(await screen.findByRole('heading', { name: 'Second' })).toBeInTheDocument()
    expect((await store.list()).map((b) => b.id)).toEqual(['b2'])
  })

  it('cannot delete the last board', async () => {
    open(new MockBoardStore([{ id: 'b1', name: 'Only', widgets: [] }]))
    await edit()
    expect(await screen.findByRole('button', { name: 'Delete board' })).toBeDisabled()
  })
})

describe('AI matching', () => {
  it('matches title or description words and ignores filler', () => {
    expect(matchCatalog('show me the customers').map((e) => e.id)).toEqual(['top-customers'])
    expect(matchCatalog('please add the')).toEqual([])
    expect(matchCatalog('zebra')).toEqual([])
  })
})

describe('refresh', () => {
  it('reloads the data after refreshMs without showing a skeleton again', async () => {
    const load = vi.fn().mockResolvedValue({ title: 'Ticker', value: 1 })
    const entry = { ...catalog[0], load }
    render(
      <UiProvider palette={synapsePalette}>
        <CatalogWidget entry={entry} data={data} refreshMs={40} />
      </UiProvider>,
    )
    expect(await screen.findByText('Ticker')).toBeInTheDocument()
    await waitFor(() => expect(load.mock.calls.length).toBeGreaterThan(2))
    expect(screen.queryByLabelText(/Loading/)).toBeNull()
  })
})
