import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, synapsePalette } from '@sami/ui'
import App from '../src/App'
import { MockBoardStore } from '../src/boards/boardStore'
import { MockAgentsClient } from '../src/ai/agentsClient'
import type { AgentAnswer } from '../src/ai/agentsClient'
import { MockIntentClient } from '../src/ai/intentClient'
import type { IntentReading } from '../src/ai/intentClient'
import { MockCatalogClient } from '../src/catalog/mockCatalogClient'
import { MockSessionClient } from '../src/session/sessionClient'

const UNREADABLE: AgentAnswer = { readable: false, problem: 'unreadable', label: null, question: null, blocks: [{ type: 'text', lines: ['Ask why a metric rose.'] }] }

const open = (store = new MockBoardStore(), agents: MockAgentsClient = new MockAgentsClient(UNREADABLE), intent: MockIntentClient = new MockIntentClient()) => {
  render(
    <UiProvider palette={synapsePalette}>
      <App client={new MockSessionClient('manager@mock-sami.com')} catalogClient={new MockCatalogClient()} agentsClient={agents} intentClient={intent} boardStore={store} history={createMemoryHistory({ initialEntries: ['/ai'] })} />
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
    expect(await screen.findByText('Ask why a metric rose.')).toBeInTheDocument()
    expect(screen.queryByText(/^Here is/)).toBeNull()
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
  question: { metric: 'sales', month: '2026-08' },
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
    const notOver: AgentAnswer = { readable: false, problem: 'not_finished', label: null, question: null, blocks: [{ type: 'text', lines: ['That month is not over yet.'] }] }
    open(new MockBoardStore(), new MockAgentsClient(notOver))
    await ask('why did sales fall this month')
    expect(await screen.findByText('That month is not over yet.')).toBeInTheDocument()
    expect(screen.queryByText(/^Here is/)).toBeNull()
  })

  it.each([
    ['restricted', 'I can only explain the whole company figure for now.'],
    ['not_one_month', 'I answer one month at a time.'],
  ] as const)('shows the %s text and no widgets', async (problem, line) => {
    const refusal: AgentAnswer = { readable: false, problem, label: null, question: null, blocks: [{ type: 'text', lines: [line] }] }
    open(new MockBoardStore(), new MockAgentsClient(refusal))
    await ask('why did sales to Acme drop in august')
    expect(await screen.findByText(line)).toBeInTheDocument()
    expect(screen.queryByText(/^Here is/)).toBeNull()
  })

  it('hands a widget request to the planner', async () => {
    const widgets: AgentAnswer = { readable: false, problem: 'widgets', label: null, question: null, blocks: [{ type: 'text', lines: ['Ask why a metric rose.'] }] }
    open(new MockBoardStore(), new MockAgentsClient(widgets))
    await ask('show me top customers')
    expect(await screen.findByText(/^Here is Top customers/)).toBeInTheDocument()
  })

  it.each(['who are you?', 'what can you do', 'tell me about our company'])('shows the agent text and no widgets for the chat question %s', async (message) => {
    open()
    await ask(message)
    expect(await screen.findByText('Ask why a metric rose.')).toBeInTheDocument()
    expect(screen.queryByText(/^Here is/)).toBeNull()
  })

  it('sends the last answered question as context with the next message', async () => {
    const agents = new MockAgentsClient(WHY)
    open(new MockBoardStore(), agents)
    await ask('what were sales for august')
    await screen.findByText('Sales fell 14.4% from July 2026 to August 2026.')
    await ask('give me the reason for the decline')
    await waitFor(() => expect(agents.calls).toHaveLength(2))
    expect(agents.calls[0].context).toBeUndefined()
    expect(agents.calls[1].context).toEqual({ metric: 'sales', month: '2026-08' })
  })

  it('does not remember a question the agent could not read', async () => {
    const agents = new MockAgentsClient(UNREADABLE)
    open(new MockBoardStore(), agents)
    await ask('zebra')
    await screen.findByText('Ask why a metric rose.')
    await ask('and again')
    await waitFor(() => expect(agents.calls).toHaveLength(2))
    expect(agents.calls[1].context).toBeUndefined()
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

const ANSWERED: IntentReading = { domain: 'Sales', domainProbability: 0.95, problem: null, reason: null, scenarios: [{ id: 'sales_top_customers', probability: 0.74, clause: 'the largest customer' }, { id: 'sales_compare_previous', probability: 0.61, clause: 'compared to July' }], didYouMean: [] }
const refusal = (reason: NonNullable<IntentReading['reason']>, didYouMean: string[] = []): IntentReading => ({ domain: 'Finance', domainProbability: 0.7, problem: 'cannot_answer', reason, scenarios: [], didYouMean })

describe('How the question was read', () => {
  it('shows the domain and every scenario with its percentage under the agent answer', async () => {
    open(new MockBoardStore(), new MockAgentsClient(WHY), new MockIntentClient(ANSWERED))
    await ask('what were sales for august')
    expect(await screen.findByText('Sales fell 14.4% from July 2026 to August 2026.')).toBeInTheDocument()
    expect(await screen.findByText('Understood as Sales (95%)')).toBeInTheDocument()
    expect(screen.getByText('Sales top customers, 74%')).toBeInTheDocument()
    expect(screen.getByText('Sales compare previous, 61%')).toBeInTheDocument()
    expect(screen.getByText('Reading preview')).toBeInTheDocument()
  })

  it.each([
    ['not_about_business', 'This does not look like a question about our figures.'],
    ['not_sure', 'I am not sure what you mean.'],
    ['no_scenarios', 'This is about Finance, which I cannot answer yet.'],
    ['nothing_matched', 'I could not tell which figure you want from Finance.'],
  ] as const)('says %s in words', async (reason, sentence) => {
    open(new MockBoardStore(), new MockAgentsClient(UNREADABLE), new MockIntentClient(refusal(reason)))
    await ask('zebra')
    expect(await screen.findByText(sentence)).toBeInTheDocument()
    expect(screen.queryByText(/Understood as/)).toBeNull()
  })

  it('suggests the nearest domains', async () => {
    open(new MockBoardStore(), new MockAgentsClient(UNREADABLE), new MockIntentClient(refusal('not_sure', ['Sales', 'Purchase'])))
    await ask('zebra')
    expect(await screen.findByText(/Did you mean Sales or Purchase\?/)).toBeInTheDocument()
  })

  it('draws the message as before when intent-api is not reachable', async () => {
    open(new MockBoardStore(), new MockAgentsClient(WHY), new MockIntentClient(new Error('down')))
    await ask('what were sales for august')
    expect(await screen.findByText('Sales fell 14.4% from July 2026 to August 2026.')).toBeInTheDocument()
    expect(screen.queryByText('Reading preview')).toBeNull()
  })

  it('shows the reading even when the analysis service is down', async () => {
    open(new MockBoardStore(), new MockAgentsClient(new Error('down')), new MockIntentClient(ANSWERED))
    await ask('what were sales for august')
    expect(await screen.findByText('The analysis service is not available right now.')).toBeInTheDocument()
    expect(await screen.findByText('Understood as Sales (95%)')).toBeInTheDocument()
  })

  it('shows the reading under a widget reply too', async () => {
    open(new MockBoardStore(), new MockAgentsClient(UNREADABLE), new MockIntentClient(ANSWERED))
    await ask('show me top customers')
    expect(await screen.findByText(/^Here is Top customers/)).toBeInTheDocument()
    expect(await screen.findByText('Understood as Sales (95%)')).toBeInTheDocument()
  })

  it('sends the question to intent-api once per message and never a @builder request', async () => {
    const intent = new MockIntentClient(ANSWERED)
    open(new MockBoardStore(), new MockAgentsClient(WHY), intent)
    await ask('what were sales for august')
    await screen.findByText('Understood as Sales (95%)')
    await ask('@builder build an inventory board')
    expect(await screen.findByRole('dialog', { name: /Inventory review/ })).toBeInTheDocument()
    expect(intent.calls).toEqual(['what were sales for august'])
  })
})
