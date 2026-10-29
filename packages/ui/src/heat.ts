const LEVELS = 8
const FLOOR = 12

export const NONE = 'none'
export const steps = Array.from({ length: LEVELS }, (_, step) => String(step))

const shade = (step: number) => `color-mix(in srgb, var(--ts-chart-1) ${Math.round(FLOOR + (step / (LEVELS - 1)) * (100 - FLOOR))}%, transparent)`

export const colorDomain = [NONE, ...steps]
export const colorRange = ['color-mix(in srgb, currentColor 7%, transparent)', ...steps.map((step) => shade(Number(step)))]

export function levelOf(value: number, low: number, high: number) {
  const span = high - low
  if (span === 0) return String(LEVELS - 3)
  return String(Math.min(LEVELS - 1, Math.floor(((value - low) / span) * LEVELS)))
}
