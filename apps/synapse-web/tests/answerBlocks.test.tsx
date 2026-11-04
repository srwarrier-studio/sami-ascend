import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { UiProvider, synapsePalette } from '@sami/ui'
import { AnswerBlocks } from '../src/ai/AnswerBlocks'
import type { AnswerBlock } from '../src/ai/answerBlocks'
import { parseBlock } from '../src/ai/answerBlocks'

const show = (blocks: AnswerBlock[]) =>
  render(
    <UiProvider palette={synapsePalette}>
      <AnswerBlocks blocks={blocks} />
    </UiProvider>,
  )

const table: AnswerBlock = {
  type: 'table',
  title: 'By customer',
  columns: ['Name', 'Current', 'Previous', 'Change', 'Share of change', 'Volume effect', 'Price effect'],
  rows: [{ key: 'A', name: 'Acme Industries', current: '100000', previous: '900000', change: '-800000', share_percent: '73.4', volume_effect: null, price_effect: null }],
}

describe('drawing the answer', () => {
  it('writes a paragraph for each text line', () => {
    show([{ type: 'text', lines: ['Sales fell 14.4%.', 'Acme Industries fell 88.9%.'] }])
    expect(screen.getByText('Sales fell 14.4%.')).toBeInTheDocument()
    expect(screen.getByText('Acme Industries fell 88.9%.')).toBeInTheDocument()
  })

  it('titles the trend chart with the metric, the months and the compared pair', () => {
    show([{ type: 'trend', metric: 'sales', currency: 'INR', points: [{ month: '2026-07', value: '7570000' }, { month: '2026-08', value: '6480000' }], marked: ['2026-07', '2026-08'] }])
    expect(screen.getByText('Sales, last 2 months (2026-07 and 2026-08 compared)')).toBeInTheDocument()
  })

  it('draws a table with money as rupees and the share as a percent', () => {
    show([table])
    expect(screen.getByText('By customer')).toBeInTheDocument()
    expect(screen.getByText('Acme Industries')).toBeInTheDocument()
    expect(screen.getByText('₹1,00,000')).toBeInTheDocument()
    expect(screen.getByText('-₹8,00,000')).toBeInTheDocument()
    expect(screen.getByText('73.4%')).toBeInTheDocument()
  })

  it('lists each evidence step and shows its rows when opened', async () => {
    show([{ type: 'evidence', finding: 'Acme Industries', steps: [{ summary: 'no valid contract for 50 days', rows: [{ SalesContract: '0040000127', ValidTo: '2026-07-12' }] }] }])
    expect(screen.getByText('Evidence: Acme Industries')).toBeInTheDocument()
    await userEvent.click(screen.getByText('no valid contract for 50 days'))
    expect(await screen.findByText('SalesContract: 0040000127 · ValidTo: 2026-07-12')).toBeInTheDocument()
  })
})

describe('reading a block', () => {
  it('gives an evidence step with no rows an empty list', () => {
    expect(parseBlock({ type: 'evidence', finding: 'A', steps: [{ summary: 's' }] })).toEqual({ type: 'evidence', finding: 'A', steps: [{ summary: 's', rows: [] }] })
  })

  it('refuses a block of an unknown or malformed shape', () => {
    expect(parseBlock({ type: 'pie' })).toBeNull()
    expect(parseBlock({ type: 'text', lines: 'no' })).toBeNull()
    expect(parseBlock(5)).toBeNull()
  })
})

const findings = {
  type: 'findings',
  headline: 'Sales of Sami-Sabinsa rose 13.7% in October 2026, to USD 113.6K from USD 99.9K in September 2026.',
  items: [
    {
      name: 'Harborline Nutrition LLC', dimension: 'customer', role: 'mover', direction: 'up', detail: 'up USD 12.4K (101.2%), 90.7% of the total rise', price_text: null,
      reasons: ['Possible reason: there was no valid contract for 43 days from 2 Aug 2026 (contract 0040000163).', 'Possible reason: production order 0001000417 ran 14 days late (due 20 Jul 2026, finished 3 Aug 2026, reason: material shortage). Behind that: purchase delivery 4500001207 ran 12 days late (due 14 Jul 2026, finished 26 Jul 2026).'],
    },
    { name: 'Pacific Wellness Pty Ltd', dimension: 'customer', role: 'offset', direction: 'down', detail: 'down USD 2.6K (11.6%)', price_text: null, reasons: [] },
  ],
  coverage: { explained_percent: '91', text: 'We can explain about 91% of the change from the data we hold; the other 9% has no cause in our data.' },
  notes: ['These are the figures of all your companies together.'],
}

describe('the why answer', () => {
  it('reads the findings block with its items and coverage', () => {
    const block = parseBlock(findings)
    expect(block?.type).toBe('findings')
    if (block?.type !== 'findings') return
    expect(block.items).toHaveLength(2)
    expect(block.items[0].detail).toBe('up USD 12.4K (101.2%), 90.7% of the total rise')
    expect(block.coverage.explainedPercent).toBe(91)
    expect(block.items[0].reasons).toHaveLength(2)
  })

  it('refuses a findings block with a malformed item', () => {
    expect(parseBlock({ ...findings, items: [{ name: 'X' }] })).toBeNull()
  })

  it('reads like a short report: headline, what moved most, what offset it, how much is explained', () => {
    show([parseBlock(findings)!])
    expect(screen.getByText(/^Sales of Sami-Sabinsa rose 13.7% in October 2026/)).toBeInTheDocument()
    expect(screen.getByText('What moved most')).toBeInTheDocument()
    expect(screen.getByText('Harborline Nutrition LLC')).toBeInTheDocument()
    expect(screen.getByText('up USD 12.4K (101.2%), 90.7% of the total rise')).toBeInTheDocument()
    expect(screen.getByText(/^Possible reason: there was no valid contract for 43 days from 2 Aug 2026/)).toBeInTheDocument()
    expect(screen.getByText(/Behind that: purchase delivery 4500001207 ran 12 days late/)).toBeInTheDocument()
    expect(screen.getByText('Partly offset by')).toBeInTheDocument()
    expect(screen.getByText('Pacific Wellness Pty Ltd')).toBeInTheDocument()
    expect(screen.getByText('How much we can explain')).toBeInTheDocument()
    expect(screen.getByRole('progressbar', { name: 'Share of the change explained' })).toBeInTheDocument()
    expect(screen.getByText(/^We can explain about 91% of the change/)).toBeInTheDocument()
    expect(screen.getByText('These are the figures of all your companies together.')).toBeInTheDocument()
  })

  it('leaves out the offset section when nothing offset the change', () => {
    show([parseBlock({ ...findings, items: [findings.items[0]] })!])
    expect(screen.queryByText('Partly offset by')).not.toBeInTheDocument()
  })
})
