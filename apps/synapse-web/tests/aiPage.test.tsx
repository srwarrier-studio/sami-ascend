import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, synapsePalette } from '@sami/ui'
import App from '../src/App'
import { MockBoardStore } from '../src/boards/boardStore'
import { MockAgentsClient } from '../src/ai/agentsClient'
import type { AgentAnswer } from '../src/ai/agentsClient'
import { MockCatalogClient } from '../src/catalog/mockCatalogClient'
import { MockSessionClient } from '../src/session/sessionClient'

const UNREADABLE: AgentAnswer = { readable: false, problem: 'unreadable', label: null, blocks: [{ type: 'text', lines: ['Ask why a metric rose.'] }] }

const open = (store = new MockBoardStore(), agents: MockAgentsClient = new MockAgentsClient(UNREADABLE)) => {
  render(
    <UiProvider palette={synapsePalette}>
      <App client={new MockSessionClient('manager@mock-sami.com')} catalogClient={new MockCatalogClient()} agentsClient={agents} boardStore={store} history={createMemoryHistory({ initialEntries: ['/ai'] })} />
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

const WHY: AgentAnswer = {
  readable: true,
  problem: null,
  label: 'Mock data (butterfly)',
  blocks: [
    { type: 'text', lines: ['Sales fell 14.4% from July 2026 to August 2026.'] },
    { type: 'trend', metric: 'sales', currency: 'INR', points: [{ month: '2026-08', value: '6480000' }], marked: ['2026-08'] },
    { type: 'evidence', finding: 'Acme Industries', steps: [{ summary: 'no valid contract for 50 days', rows: [] }] },
  ],
}

describe('answers from the agent', () => {
  it('shows the text, the chart, the evidence and the label for a readable question', async () => {
    open(new MockBoardStore(), new MockAgentsClient(WHY))
    await ask('why did sales fall in August')
    expect(await screen.findByText('Sales fell 14.4% from July 2026 to August 2026.')).toBeInTheDocument()
    expect(screen.getByText('Evidence: Acme Industries')).toBeInTheDocument()
    expect(screen.getByText('Mock data (butterfly)')).toBeInTheDocument()
    expect(screen.queryByText(/^Here is/)).toBeNull()
  })

  it('falls back to the widgets when the agent cannot read the question', async () => {
    open()
    await ask('show me top customers')
    expect(await screen.findByText(/^Here is Top customers/)).toBeInTheDocument()
    expect(screen.queryByText('Ask why a metric rose.')).toBeNull()
  })

  it('shows the not-over text and no widgets', async () => {
    const notOver: AgentAnswer = { readable: false, problem: 'not_finished', label: null, blocks: [{ type: 'text', lines: ['That month is not over yet.'] }] }
    open(new MockBoardStore(), new MockAgentsClient(notOver))
    await ask('why did sales fall this month')
    expect(await screen.findByText('That month is not over yet.')).toBeInTheDocument()
    expect(screen.queryByText(/^Here is/)).toBeNull()
  })

  it('never sends @builder messages to the agent', async () => {
    open(new MockBoardStore(), new MockAgentsClient(WHY))
    await ask('@builder build an inventory board')
    expect(await screen.findByRole('dialog', { name: /Inventory review/ })).toBeInTheDocument()
    expect(screen.queryByText('Sales fell 14.4% from July 2026 to August 2026.')).toBeNull()
  })

  it('says the service is unavailable and keeps the thread usable', async () => {
    open(new MockBoardStore(), new MockAgentsClient(new Error('down')))
    await ask('why did sales fall in August')
    expect(await screen.findByText('The analysis service is not available right now.')).toBeInTheDocument()
    expect(screen.queryByText(/^Here is/)).toBeNull()
    expect(screen.getByLabelText('Message')).toBeEnabled()
  })
})
