import { render } from '@testing-library/react'
import { BarChart, formatValue, LineChart, UiProvider, workspacePalette } from '../src'

const data = [
  { label: 'Mon', value: 10 },
  { label: 'Tue', value: 20 },
  { label: 'Wed', value: 15 },
]

function show(element: React.ReactElement) {
  return render(<UiProvider palette={workspacePalette}>{element}</UiProvider>)
}

describe('LineChart', () => {
  it('renders an svg with a title', () => {
    const { container, getByText } = show(<LineChart data={data} title="Day sales" />)
    expect(container.querySelector('svg')).not.toBeNull()
    expect(getByText('Day sales')).toBeInTheDocument()
  })

  it('shows No data for an empty array', () => {
    const { getByText, container } = show(<LineChart data={[]} />)
    expect(getByText('No data')).toBeInTheDocument()
    expect(container.querySelector('svg')).toBeNull()
  })
})

describe('BarChart', () => {
  it('renders one bar per data point', () => {
    const { container } = show(<BarChart data={data} />)
    expect(container.querySelectorAll('svg g.ts-chart__bar rect').length).toBe(3)
  })

  it('shows No data for an empty array', () => {
    expect(show(<BarChart data={[]} />).getByText('No data')).toBeInTheDocument()
  })
})

describe('formatValue', () => {
  it('formats a number', () => expect(formatValue(1234.5)).toBe('1,234.5'))
  it('formats currency in rupees', () => expect(formatValue(1234.5, 'currency')).toBe('₹1,235'))
  it('formats a fraction as percent', () => expect(formatValue(0.125, 'percent')).toBe('12.5%'))
})
