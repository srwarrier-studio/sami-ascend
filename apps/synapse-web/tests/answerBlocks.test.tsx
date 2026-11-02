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
