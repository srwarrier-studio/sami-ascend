import { render } from '@testing-library/react'
import { drawFlow } from '../src/login/drawFlow'
import { ProcessFlow } from '../src/login/ProcessFlow'
import { links, pointOn, stations } from '../src/login/flow'
import { CYCLE, HOP, TRAVEL, arrivalsAt, departures, glowLevel, travelProgress } from '../src/login/timeline'

describe('the process layout', () => {
  it('has the five stations of the purchase flow in order', () => {
    expect(stations.map((station) => station.id)).toEqual(['requisition', 'order', 'receipt', 'invoice', 'payment'])
  })

  it('joins each station to the next', () => {
    expect(links).toHaveLength(stations.length - 1)
    links.forEach((link, index) => {
      expect(link.from).toBe(stations[index])
      expect(link.to).toBe(stations[index + 1])
    })
  })

  it('moves a card from one station to the next along the line', () => {
    expect(pointOn(links[0], 0)).toEqual({ x: stations[0].x, y: stations[0].y })
    expect(pointOn(links[0], 1)).toEqual({ x: stations[1].x, y: stations[1].y })
  })
})

describe('the timeline', () => {
  it('travels from 0 to 1 and rests after', () => {
    expect(travelProgress(0, 0)).toBe(0)
    expect(travelProgress(TRAVEL / 2, 0)).toBeCloseTo(0.5)
    expect(travelProgress(TRAVEL + 0.1, 0)).toBeNull()
  })

  it('repeats every cycle', () => {
    expect(travelProgress(CYCLE + TRAVEL / 2, 0)).toBeCloseTo(0.5)
  })

  it('starts each hop when the previous card arrives', () => {
    expect(departures(1)[0]).toBe(HOP)
    expect(arrivalsAt(1)[0]).toBeCloseTo(TRAVEL)
    expect(departures(1)[0]).toBeGreaterThanOrEqual(arrivalsAt(1)[0])
  })

  it('has two batches per link', () => {
    links.forEach((_, index) => expect(departures(index)).toHaveLength(2))
  })

  it('glows up then fades out', () => {
    expect(glowLevel(0, 0)).toBe(0)
    expect(glowLevel(CYCLE * 0.02, 0)).toBeCloseTo(1)
    expect(glowLevel(CYCLE * 0.5, 0)).toBe(0)
  })
})

describe('the drawing', () => {
  it('is a canvas hidden from assistive technology', () => {
    const { container } = render(<ProcessFlow animated={false} />)
    const canvas = container.querySelector('canvas')
    expect(canvas).toHaveAttribute('aria-hidden', 'true')
    expect(canvas).toHaveAttribute('data-animated', 'false')
  })

  it('says when it is animated', () => {
    const { container } = render(<ProcessFlow animated />)
    expect(container.querySelector('canvas')).toHaveAttribute('data-animated', 'true')
  })
})

const recorder = () => {
  const calls: string[] = []
  const ctx = new Proxy({}, { get: (_, name: string) => (name === 'roundRect' ? () => calls.push(name) : () => undefined), set: () => true })
  return { ctx: ctx as unknown as CanvasRenderingContext2D, calls }
}

const colors = { ground: 'black', line: 'green', glow: 'lime', card: 'white', ink: 'silver' }

describe('drawFlow', () => {
  it('draws no cards when still', () => {
    const still = recorder()
    drawFlow(still.ctx, colors, 800, 600, TRAVEL / 2, false)
    const moving = recorder()
    drawFlow(moving.ctx, colors, 800, 600, TRAVEL / 2, true)
    expect(moving.calls.length).toBeGreaterThan(still.calls.length)
  })

  it('draws the same still frame at any time', () => {
    const early = recorder()
    drawFlow(early.ctx, colors, 800, 600, 0, false)
    const late = recorder()
    drawFlow(late.ctx, colors, 800, 600, 9, false)
    expect(late.calls).toEqual(early.calls)
  })

  it('draws without error at any time of the cycle', () => {
    for (let time = 0; time < CYCLE * 2; time += 0.7) {
      const { ctx } = recorder()
      expect(() => drawFlow(ctx, colors, 800, 600, time, true)).not.toThrow()
    }
  })
})
