import { cascades } from './network'

export const CYCLE = 14
export const TRAVEL = 1.6
const HOP = 1.9
const SECOND_CASCADE_START = 7.5
export const DRIFT = 6

export const hopsFrom = (neuronIndex: number) =>
  cascades.flatMap((cascade, order) => {
    const step = cascade.indexOf(neuronIndex)
    return step < 0 ? [] : [(order === 0 ? 0 : SECOND_CASCADE_START) + step * HOP]
  })

const since = (time: number, begin: number) => (((time - begin) % CYCLE) + CYCLE) % CYCLE

export const pulseProgress = (time: number, begin: number) => {
  const local = since(time, begin)
  return local < TRAVEL ? local / TRAVEL : null
}

export const flashLevel = (time: number, begin: number) => {
  const part = since(time, begin) / CYCLE
  if (part < 0.02) return part / 0.02
  if (part < 0.12) return 1 - (part - 0.02) / 0.1
  return 0
}

export const drift = (index: number, time: number) => {
  const turn = (Math.PI * 2 * time) / (14 + index * 2.4)
  return { x: Math.sin(turn + index * 2.3) * DRIFT, y: Math.cos(turn * 0.8 + index * 1.9) * DRIFT }
}
