import { links } from './flow'

export const CYCLE = 14
export const TRAVEL = 1.9
export const HOP = 2
const BATCH_STARTS = [0, 7]

export const departures = (linkIndex: number) => BATCH_STARTS.map((start) => start + linkIndex * HOP)

export const arrivalsAt = (stationIndex: number) =>
  stationIndex === 0 ? BATCH_STARTS : departures(stationIndex - 1).map((begin) => begin + TRAVEL)

const since = (time: number, begin: number) => (((time - begin) % CYCLE) + CYCLE) % CYCLE

const ease = (t: number) => t * t * (3 - 2 * t)

export const travelProgress = (time: number, begin: number) => {
  const local = since(time, begin)
  return local < TRAVEL ? ease(local / TRAVEL) : null
}

export const glowLevel = (time: number, begin: number) => {
  const part = since(time, begin) / CYCLE
  if (part < 0.02) return part / 0.02
  if (part < 0.14) return 1 - (part - 0.02) / 0.12
  return 0
}

export const lastDeparture = links.length * HOP + BATCH_STARTS[BATCH_STARTS.length - 1]
