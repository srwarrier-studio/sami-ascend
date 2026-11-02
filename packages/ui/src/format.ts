export type ValueFormat = 'number' | 'currency' | 'percent' | `currency:${string}`

const CODE_PREFIX = 'currency:'

export const isCurrency = (format?: ValueFormat) => format === 'currency' || format?.startsWith(CODE_PREFIX) === true

const codeOf = (format: ValueFormat) => (format.startsWith(CODE_PREFIX) ? format.slice(CODE_PREFIX.length) : 'INR')

const byCode = new Map<string, Intl.NumberFormat>()

const currencyFor = (code: string) => {
  let formatter = byCode.get(code)
  if (!formatter) {
    formatter = new Intl.NumberFormat('en-IN', { style: 'currency', currency: code, maximumFractionDigits: 0 })
    byCode.set(code, formatter)
  }
  return formatter
}

const symbolOf = (code: string) => currencyFor(code).formatToParts(0).find((part) => part.type === 'currency')?.value ?? code

const formatters = {
  number: new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }),
  percent: new Intl.NumberFormat('en-IN', { style: 'percent', maximumFractionDigits: 1 }),
}

export function formatValue(value: number, format: ValueFormat = 'number') {
  if (isCurrency(format)) return currencyFor(codeOf(format)).format(value)
  return formatters[format as 'number' | 'percent'].format(value)
}

const compact = new Intl.NumberFormat('en-IN', { notation: 'compact', maximumFractionDigits: 1 })
const compactWhole = new Intl.NumberFormat('en-IN', { notation: 'compact', maximumFractionDigits: 0 })
const SMALLEST_WHOLE = 1000

export function formatCompact(value: number, format: ValueFormat = 'number', whole = false) {
  if (format === 'percent') return formatValue(value, 'percent')
  const shortened = whole && Math.abs(value) >= SMALLEST_WHOLE ? compactWhole : compact
  return `${isCurrency(format) ? symbolOf(codeOf(format)) : ''}${shortened.format(value)}`
}

const signedPercent = new Intl.NumberFormat('en-IN', { style: 'percent', maximumFractionDigits: 1, signDisplay: 'exceptZero' })

export function formatDelta(value: number) {
  return signedPercent.format(value)
}
