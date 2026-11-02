import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryHistory } from '@tanstack/react-router'
import { UiProvider, synapsePalette } from '@sami/ui'
import App from '../src/App'
import { MockBoardStore } from '../src/boards/boardStore'
import { MockIntentClient } from '../src/ai/intentClient'
import { IntentDataUnavailable } from '../src/ai/intentClient'
import type { IntentAnswer, IntentReading, IntentReply, ReplyReason } from '../src/ai/intentClient'
import { MockCatalogClient } from '../src/catalog/mockCatalogClient'
import { MockSessionClient } from '../src/session/sessionClient'

const open = (store = new MockBoardStore(), intent: MockIntentClient = new MockIntentClient()) => {
  render(
    <UiProvider palette={synapsePalette}>
      <App client={new MockSessionClient('manager@mock-sami.com')} catalogClient={new MockCatalogClient()} intentClient={intent} boardStore={store} history={createMemoryHistory({ initialEntries: ['/ai'] })} />
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
    expect(await screen.findByText(/^I could not match that/)).toBeInTheDocument()
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

const WHY: IntentAnswer = {
  scenario: 'sales_why',
  blocks: [
    { type: 'text', lines: ['Sales fell 14.4% from July 2026 to August 2026.'] },
    { type: 'trend', metric: 'sales', currency: 'USD', points: [{ month: '2026-08', value: '6480000' }], marked: ['2026-08'] },
    { type: 'evidence', finding: 'Harborline Nutrition LLC', steps: [{ summary: 'no valid contract for 50 days', rows: [] }] },
  ],
}

const ANSWERED: IntentReading = { domain: 'Sales', domainProbability: 0.95, problem: null, reason: null, scenarios: [{ id: 'sales_top_customers', probability: 0.74, clause: 'the largest customer' }, { id: 'sales_compare_previous', probability: 0.61, clause: 'compared to July' }], didYouMean: [] }
const refusal = (reason: NonNullable<IntentReading['reason']>, didYouMean: string[] = []): IntentReading => ({ domain: 'Finance', domainProbability: 0.7, problem: 'cannot_answer', reason, scenarios: [], didYouMean })

const replyFor = (reading: IntentReading, answers: IntentAnswer[] = [], reason: ReplyReason | null = reading.reason, periods: string[] = []): IntentReply => ({
  reading,
  problem: answers.length > 0 ? null : reading.problem ?? (reason ? 'cannot_answer' : null),
  reason: answers.length > 0 ? null : reason,
  periods,
  answers,
})

describe('How the question was read', () => {
  it('shows the domain and every scenario with its percentage under the answer', async () => {
    open(new MockBoardStore(), new MockIntentClient(replyFor(ANSWERED, [WHY])))
    await ask('what were sales for august')
    expect(await screen.findByText('Sales fell 14.4% from July 2026 to August 2026.')).toBeInTheDocument()
    expect(await screen.findByText('Understood as Sales (95%)')).toBeInTheDocument()
    expect(screen.getByText('Sales top customers, 74%')).toBeInTheDocument()
    expect(screen.getByText('Sales compare previous, 61%')).toBeInTheDocument()
    expect(screen.getByText('Reading')).toBeInTheDocument()
  })

  it.each([
    ['not_about_business', 'This does not look like a question about our figures.'],
    ['not_sure', 'I am not sure what you mean.'],
    ['no_scenarios', 'This is about Finance, which I cannot answer yet.'],
    ['nothing_matched', 'I could not tell which figure you want from Finance.'],
  ] as const)('says %s in words', async (reason, sentence) => {
    open(new MockBoardStore(), new MockIntentClient(replyFor(refusal(reason))))
    await ask('zebra')
    expect(await screen.findByText(sentence)).toBeInTheDocument()
    expect(screen.queryByText(/Understood as/)).toBeNull()
  })

  it('suggests the nearest domains', async () => {
    open(new MockBoardStore(), new MockIntentClient(replyFor(refusal('not_sure', ['Sales', 'Purchase']))))
    await ask('zebra')
    expect(await screen.findByText(/Did you mean Sales or Purchase\?/)).toBeInTheDocument()
  })

  it('draws the widget reply with no reading when intent-api is not reachable', async () => {
    open(new MockBoardStore(), new MockIntentClient(new Error('down')))
    await ask('show me top customers')
    expect(await screen.findByText(/^Here is Top customers/)).toBeInTheDocument()
    expect(screen.queryByText('Reading')).toBeNull()
  })

  it('shows the reading under a widget reply too', async () => {
    open(new MockBoardStore(), new MockIntentClient(replyFor(ANSWERED)))
    await ask('show me top customers')
    expect(await screen.findByText(/^Here is Top customers/)).toBeInTheDocument()
    expect(await screen.findByText('Understood as Sales (95%)')).toBeInTheDocument()
  })

  it('drops the refusal when widgets answered after the refusal', async () => {
    open(new MockBoardStore(), new MockIntentClient(replyFor(refusal('no_scenarios', ['Sales']))))
    await ask('show me top customers')
    expect(await screen.findByText(/^Here is Top customers/)).toBeInTheDocument()
    expect(await screen.findByText('Understood as Finance (70%)')).toBeInTheDocument()
    expect(screen.queryByText(/cannot answer yet/)).toBeNull()
    expect(screen.queryByText(/Did you mean/)).toBeNull()
  })

  it('shows the badge only when no domain was read and widgets answered', async () => {
    const unread: IntentReading = { ...refusal('not_sure'), domain: null }
    open(new MockBoardStore(), new MockIntentClient(replyFor(unread)))
    await ask('show me top customers')
    expect(await screen.findByText(/^Here is Top customers/)).toBeInTheDocument()
    expect(screen.getByText('Reading')).toBeInTheDocument()
    expect(screen.queryByText(/Understood as/)).toBeNull()
  })

  it('sends the question to intent-api once per message and never a @builder request', async () => {
    const intent = new MockIntentClient(replyFor(ANSWERED, [WHY]))
    open(new MockBoardStore(), intent)
    await ask('what were sales for august')
    await screen.findByText('Understood as Sales (95%)')
    await ask('@builder build an inventory board')
    expect(await screen.findByRole('dialog', { name: /Inventory review/ })).toBeInTheDocument()
    expect(intent.calls).toEqual(['what were sales for august'])
  })
})

const BLOCK_TEXT = (line: string): IntentAnswer['blocks'][number] => ({ type: 'text', lines: [line] })
const TABLE: IntentAnswer['blocks'][number] = { type: 'table', title: 'Top customers, June 2026', columns: ['Name', 'Current'], rows: [{ name: 'Kestrel Logistics', current: '400' }] }
const TREND: IntentAnswer['blocks'][number] = { type: 'trend', metric: 'sales', currency: 'INR', points: [{ month: '2026-05', value: '500' }, { month: '2026-06', value: '600' }], marked: [] }

describe('Answers from intent-api', () => {
  it('draws a ranking as a sentence and a table with the card', async () => {
    open(new MockBoardStore(), new MockIntentClient(replyFor(ANSWERED, [{ scenario: 'sales_top_customers', blocks: [BLOCK_TEXT('Kestrel Logistics led sales in June 2026 at INR 400.'), TABLE] }])))
    await ask('to whom did we sell the most in June')
    expect(await screen.findByText('Kestrel Logistics led sales in June 2026 at INR 400.')).toBeInTheDocument()
    expect(screen.getByText('Top customers, June 2026')).toBeInTheDocument()
    expect(screen.getByText('Understood as Sales (95%)')).toBeInTheDocument()
  })

  it('draws a value as one sentence and no chart', async () => {
    open(new MockBoardStore(), new MockIntentClient(replyFor(ANSWERED, [{ scenario: 'sales_value', blocks: [BLOCK_TEXT('Sales for June 2026 were INR 600.')] }])))
    await ask('how much did we sell in June')
    expect(await screen.findByText('Sales for June 2026 were INR 600.')).toBeInTheDocument()
    expect(screen.queryByRole('table')).toBeNull()
    expect(screen.queryByText(/Sales, last/)).toBeNull()
  })

  it('draws a trend as a sentence and a chart', async () => {
    open(new MockBoardStore(), new MockIntentClient(replyFor(ANSWERED, [{ scenario: 'sales_trend', blocks: [BLOCK_TEXT('Sales went up 20.0% from 2026-05 to 2026-06.'), TREND] }])))
    await ask('sales trend')
    expect(await screen.findByText('Sales went up 20.0% from 2026-05 to 2026-06.')).toBeInTheDocument()
    expect(screen.getByText(/Sales, last 2 months/)).toBeInTheDocument()
  })

  it('draws two answers in the order returned', async () => {
    open(new MockBoardStore(), new MockIntentClient(replyFor(ANSWERED, [
      { scenario: 'sales_top_customers', blocks: [BLOCK_TEXT('First answer.')] },
      { scenario: 'sales_trend', blocks: [BLOCK_TEXT('Second answer.')] },
    ])))
    await ask('top customers and the trend')
    const first = await screen.findByText('First answer.')
    const second = screen.getByText('Second answer.')
    expect(first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  it('says which periods it read and says nothing else when the period cannot be used', async () => {
    open(new MockBoardStore(), new MockIntentClient(replyFor(ANSWERED, [], 'period_not_supported', ['June 2026', 'May 2026'])))
    await ask('sales in june and in may')
    expect(await screen.findByText('I could not use the period in your question (I read June 2026 and May 2026). Ask for one period that has already started.')).toBeInTheDocument()
    expect(screen.getByText('Understood as Sales (95%)')).toBeInTheDocument()
  })

  it('says the figures are not available when synapse-api cannot be reached', async () => {
    open(new MockBoardStore(), new MockIntentClient(new IntentDataUnavailable('down')))
    await ask('how much did we sell in June')
    expect(await screen.findByText('The figures are not available right now.')).toBeInTheDocument()
  })

  it('draws a why answer with its chart and evidence', async () => {
    open(new MockBoardStore(), new MockIntentClient(replyFor(ANSWERED, [WHY])))
    await ask('why did sales fall in august')
    expect(await screen.findByText('Sales fell 14.4% from July 2026 to August 2026.')).toBeInTheDocument()
    expect(screen.getByText('Evidence: Harborline Nutrition LLC')).toBeInTheDocument()
    expect(screen.getByText('Understood as Sales (95%)')).toBeInTheDocument()
  })

  it('hands a question with no answer yet to the widget planner and keeps the card', async () => {
    open(new MockBoardStore(), new MockIntentClient(replyFor(ANSWERED, [], 'not_answerable_yet')))
    await ask('show me top customers')
    expect(await screen.findByText(/^Here is Top customers/)).toBeInTheDocument()
    expect(screen.getByText('Understood as Sales (95%)')).toBeInTheDocument()
  })

  it('sends the chosen company with the question', async () => {
    const intent = new MockIntentClient(replyFor(ANSWERED, [WHY]))
    open(new MockBoardStore(), intent)
    await ask('why did sales fall in august')
    await screen.findByText('Sales fell 14.4% from July 2026 to August 2026.')
    expect(intent.companies).toEqual(['sabinsa'])
  })
})
