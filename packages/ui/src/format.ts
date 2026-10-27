export type ValueFormat = 'number' | 'currency' | 'percent'

const formatters: Record<ValueFormat, Intl.NumberFormat> = {
  number: new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }),
  currency: new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }),
  percent: new Intl.NumberFormat('en-IN', { style: 'percent', maximumFractionDigits: 1 }),
}

export function formatValue(value: number, format: ValueFormat = 'number') {
  return formatters[format].format(value)
}
