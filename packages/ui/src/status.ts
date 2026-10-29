import type { Tone } from './polarCharts'

const positive = ['paid', 'complete', 'completed', 'delivered', 'approved', 'done']
const negative = ['overdue', 'blocked', 'failed', 'cancelled', 'canceled', 'rejected']
const caution = ['due', 'pending', 'partial', 'on hold', 'waiting']

export function statusTone(status: string): Tone {
  const name = status.trim().toLowerCase()
  if (positive.includes(name)) return 'positive'
  if (negative.includes(name)) return 'negative'
  if (caution.includes(name)) return 'caution'
  return 'neutral'
}
