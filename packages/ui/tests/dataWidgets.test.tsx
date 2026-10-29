import { render, screen } from '@testing-library/react'
import { DataTable, RankedList, UiProvider, workspacePalette } from '../src'
import { statusTone } from '../src/status'

function show(element: React.ReactElement) {
  return render(<UiProvider palette={workspacePalette}>{element}</UiProvider>)
}

const bars = () => screen.getAllByRole('progressbar').map((bar) => Number(bar.getAttribute('aria-valuenow')))

describe('RankedList bars', () => {
  it('sizes each bar against the first item', () => {
    show(<RankedList title="Top" items={[{ label: 'A', value: 200 }, { label: 'B', value: 100 }, { label: 'C', value: 50 }]} />)
    expect(bars()).toEqual([100, 50, 25])
  })

  it('draws empty bars when every value is zero', () => {
    show(<RankedList title="Top" items={[{ label: 'A', value: 0 }, { label: 'B', value: 0 }]} />)
    expect(bars()).toEqual([0, 0])
  })

  it('treats a negative value as an empty bar', () => {
    show(<RankedList title="Top" items={[{ label: 'A', value: 10 }, { label: 'B', value: -5 }]} />)
    expect(bars()).toEqual([100, 0])
  })

  it('numbers the rows from one', () => {
    show(<RankedList title="Top" items={[{ label: 'A', value: 2 }, { label: 'B', value: 1 }]} />)
    expect(screen.getByText('1. A')).toBeInTheDocument()
    expect(screen.getByText('2. B')).toBeInTheDocument()
  })

  it('shows No data without items', () => {
    show(<RankedList title="Top" items={[]} />)
    expect(screen.getByText('No data')).toBeInTheDocument()
  })
})

const columns = [
  { key: 'customer', label: 'Customer', format: 'text' as const },
  { key: 'status', label: 'Status', format: 'status' as const },
  { key: 'amount', label: 'Amount', format: 'currency' as const },
]

const rows = [
  { customer: 'Northwind', status: 'Paid', amount: 84200 },
  { customer: 'Alder', status: 'Overdue', amount: 66300 },
  { customer: 'Harbor', status: 'Open', amount: 71950 },
]

describe('DataTable', () => {
  it('aligns number columns to the right and text columns to the left', () => {
    show(<DataTable columns={columns} rows={rows} />)
    expect(screen.getByText('Amount').getAttribute('style')).toContain('right')
    expect(screen.getByText('Customer').getAttribute('style') ?? '').not.toContain('right')
  })

  it('shows a coloured tag for a status column', () => {
    show(<DataTable columns={columns} rows={rows} />)
    expect(screen.getByText('Paid').getAttribute('data-tone')).toBe('positive')
    expect(screen.getByText('Overdue').getAttribute('data-tone')).toBe('negative')
    expect(screen.getByText('Open').getAttribute('data-tone')).toBe('neutral')
  })

  it('formats currency and leaves a missing value empty', () => {
    show(<DataTable columns={columns} rows={[{ customer: 'Alder', status: null, amount: 66300 }]} />)
    expect(screen.getByText('₹66,300')).toBeInTheDocument()
  })
})

describe('statusTone', () => {
  it.each([
    ['Paid', 'positive'],
    ['DELIVERED', 'positive'],
    ['Overdue', 'negative'],
    ['Cancelled', 'negative'],
    ['Pending', 'caution'],
    ['On hold', 'caution'],
    ['Open', 'neutral'],
    ['Something new', 'neutral'],
  ])('reads %s as %s', (status, tone) => {
    expect(statusTone(status)).toBe(tone)
  })
})
