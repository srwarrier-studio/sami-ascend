import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, synapsePalette } from '@sami/ui'
import App from '../src/App'
import { MockBoardStore } from '../src/boards/boardStore'
import { MockSalesData } from '../src/data/mockSalesData'
import { MockSessionClient } from '../src/session/sessionClient'

const open = (store = new MockBoardStore()) => {
  render(
    <UiProvider palette={synapsePalette}>
      <App client={new MockSessionClient('manager@mock-sami.com')} salesData={new MockSalesData(new Date('2026-10-29T10:00:00Z'))} boardStore={store} history={createMemoryHistory({ initialEntries: ['/ai'] })} />
    </UiProvider>,
  )
  return store
}

const ask = async (message: string) => {
  await userEvent.type(await screen.findByLabelText('Message'), message)
  await userEvent.click(screen.getByRole('button', { name: 'Send' }))
}

describe('AI chat', () => {
  it('starts with a welcome and example prompts that send themselves', async () => {
    open()
    expect(await screen.findByText('Ask for what you want to see')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Show top customers and top materials' }))
    expect(await screen.findByText(/^Here is Top customers/)).toBeInTheDocument()
  })

  it('shows your message and a reply that carries the widgets', async () => {
    open()
    await ask('show me top customers')
    expect(await screen.findByText('show me top customers')).toBeInTheDocument()
    expect(await screen.findByText(/^Here is Top customers/)).toBeInTheDocument()
    await waitFor(() => expect(screen.getAllByText(/Top customers/).length).toBeGreaterThan(1))
  })

  it('says so when nothing matches', async () => {
    open()
    await ask('zebra')
    expect(await screen.findByText(/could not match/)).toBeInTheDocument()
  })
})

describe('@builder', () => {
  it('opens the built board in a modal, which closes and reopens from the message', async () => {
    open()
    await ask('@builder build an inventory board')
    const modal = await screen.findByRole('dialog', { name: /Inventory review/ })
    expect(modal).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Close' }))
    await userEvent.click(await screen.findByRole('button', { name: 'Open board' }))
    expect(await screen.findByRole('dialog', { name: /Inventory review/ })).toBeInTheDocument()
  })

  it('turns @builder into a tag in the box and keeps it in the sent message', async () => {
    open()
    await userEvent.type(await screen.findByLabelText('Message'), '@builder ')
    expect(screen.getByLabelText('Message')).toHaveValue('')
    expect(screen.getByText('@builder')).toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('Message'), 'build an inventory board')
    await userEvent.click(screen.getByRole('button', { name: 'Send' }))
    expect(await screen.findByRole('dialog', { name: /Inventory review/ })).toBeInTheDocument()
    expect(screen.getAllByText('@builder').length).toBeGreaterThan(0)
  })

  it('removes the tag with backspace on an empty box', async () => {
    open()
    const box = await screen.findByLabelText('Message')
    await userEvent.type(box, '@builder ')
    await userEvent.type(box, '{Backspace}')
    expect(screen.queryByText('@builder')).toBeNull()
  })

  it('explains what to ask when there is nothing to build', async () => {
    open()
    await ask('@builder')
    expect(await screen.findByText(/Tell me what to build/)).toBeInTheDocument()
    expect(screen.queryByRole('dialog')).toBeNull()
  })
})

describe('AI page as a full screen', () => {
  it('hides the app navigation and goes back to the boards', async () => {
    open()
    await screen.findByLabelText('Message')
    expect(screen.queryByText('My boards')).toBeNull()
    await userEvent.click(screen.getByRole('button', { name: 'Back to boards' }))
    expect(await screen.findByText('My boards')).toBeInTheDocument()
  })
})

describe('saving the built board', () => {
  const saveDialog = async () => {
    await ask('@builder build an inventory board')
    await userEvent.click(await screen.findByRole('button', { name: 'Save as board' }))
    return screen.findByRole('dialog', { name: 'Save as board' })
  }

  it('creates a new board under the limit and opens it', async () => {
    const store = open()
    await saveDialog()
    expect(screen.getByLabelText('Board name')).toHaveValue('Inventory review')
    await userEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(await screen.findByRole('tab', { name: 'Inventory review' })).toHaveAttribute('aria-selected', 'true')
    const boards = await store.list()
    expect(boards).toHaveLength(2)
    expect(boards[1].widgets.length).toBeGreaterThan(1)
  })

  it('at three boards asks which to replace and changes nothing until confirmed', async () => {
    const store = open(
      new MockBoardStore([
        { id: 'a', name: 'Alpha', widgets: [{ id: 'w1', catalogId: 'sales-today' }] },
        { id: 'b', name: 'Beta', widgets: [] },
        { id: 'c', name: 'Gamma', widgets: [] },
      ]),
    )
    await saveDialog()
    expect(await screen.findByText(/You have 3 boards/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Replace board' })).toBeDisabled()
    await userEvent.click(screen.getByRole('radio', { name: 'Alpha' }))
    expect(await store.list()).toHaveLength(3)
    expect((await store.list())[0].widgets).toHaveLength(1)
    await userEvent.click(screen.getByRole('button', { name: 'Replace Alpha' }))
    expect(await screen.findByRole('tab', { name: 'Inventory review' })).toBeInTheDocument()
    const boards = await store.list()
    expect(boards).toHaveLength(3)
    expect(boards[0].name).toBe('Inventory review')
    expect(boards[0].widgets.length).toBeGreaterThan(1)
  })
})
