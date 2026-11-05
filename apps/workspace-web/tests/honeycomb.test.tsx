import { render } from '@testing-library/react'
import { Honeycomb } from '../src/login/Honeycomb'
import { drawHoneycomb } from '../src/login/drawHoneycomb'
import { FrameMeter } from '../src/login/frameMeter'
import { cellsFor, fluxLevel, radiusFor, twinkleLevel } from '../src/login/honeycomb'

describe('the honeycomb layout', () => {
  it('covers the whole canvas, with cells just past each edge', () => {
    const cells = cellsFor(1200, 800)
    const xs = cells.map((cell) => cell.x)
    const ys = cells.map((cell) => cell.y)
    expect(Math.min(...xs)).toBeLessThan(0)
    expect(Math.max(...xs)).toBeGreaterThan(1200)
    expect(Math.min(...ys)).toBeLessThan(0)
    expect(Math.max(...ys)).toBeGreaterThan(800 - radiusFor(1200) * 2)
  })

  it('offsets every other row by half a cell', () => {
    const cells = cellsFor(1200, 800)
    const rowAt = (y: number) => cells.filter((cell) => cell.y === y)
    expect(rowAt(1.5 * radiusFor(1200))[0].x - rowAt(0)[0].x).toBeCloseTo((Math.sqrt(3) * radiusFor(1200)) / 2)
  })

  it('keeps cells a readable size on small screens', () => {
    expect(radiusFor(200)).toBe(18)
  })
})

describe('the twinkle', () => {
  const cells = cellsFor(1200, 800).length
  const litAt = (time: number) => Array.from({ length: cells }, (_, index) => twinkleLevel(index, time)).filter((level) => level >= 0.12).length

  it('stays between dark and fully lit', () => {
    for (let time = 0; time < 40; time += 0.9) {
      for (let index = 0; index < cells; index++) {
        const level = twinkleLevel(index, time)
        expect(level).toBeGreaterThanOrEqual(0)
        expect(level).toBeLessThanOrEqual(1)
      }
    }
  })

  it('lights a small share of the cells at any moment, never all and never none', () => {
    for (let time = 0; time < 40; time += 3.7) {
      expect(litAt(time)).toBeGreaterThan(0)
      expect(litAt(time)).toBeLessThan(cells * 0.3)
    }
  })

  it('turns a cell on and off again, on its own timing', () => {
    const index = Array.from({ length: cells }, (_, i) => i).find((i) => twinkleLevel(i, 0) === 0 && Array.from({ length: 700 }, (__, step) => twinkleLevel(i, step * 0.1)).some((level) => level > 0.9))!
    const levels = Array.from({ length: 700 }, (_, step) => twinkleLevel(index, step * 0.1))
    expect(Math.max(...levels)).toBeGreaterThan(0.9)
    expect(levels.filter((level) => level === 0).length).toBeGreaterThan(200)
  })

  it('changes smoothly, with no sudden flash', () => {
    for (let index = 0; index < 60; index++) {
      for (let time = 0; time < 60; time += 0.04) {
        expect(Math.abs(twinkleLevel(index, time + 0.04) - twinkleLevel(index, time))).toBeLessThan(0.05)
      }
    }
  })

  it('gives each cell its own rhythm', () => {
    const series = (index: number) => Array.from({ length: 40 }, (_, step) => twinkleLevel(index, step * 0.5).toFixed(2)).join()
    const distinct = new Set(Array.from({ length: 30 }, (_, index) => series(index)))
    expect(distinct.size).toBeGreaterThan(5)
  })
})

describe('the flux', () => {
  it('stays between dark and fully lit', () => {
    for (let time = 0; time < 60; time += 1.7) {
      for (let u = 0; u <= 1; u += 0.1) {
        const level = fluxLevel(u, 1 - u, time)
        expect(level).toBeGreaterThanOrEqual(0)
        expect(level).toBeLessThanOrEqual(1)
      }
    }
  })

  it('moves the light over time without a restart', () => {
    expect(fluxLevel(0.3, 0.4, 0)).not.toBeCloseTo(fluxLevel(0.3, 0.4, 5))
    const steps = [0, 0.1, 0.2, 0.3].map((time) => fluxLevel(0.3, 0.4, time))
    steps.slice(1).forEach((level, index) => expect(Math.abs(level - steps[index])).toBeLessThan(0.05))
  })

  it('lights different cells differently at the same moment', () => {
    expect(fluxLevel(0.1, 0.1, 3)).not.toBeCloseTo(fluxLevel(0.6, 0.8, 3))
  })
})

const recorder = () => {
  const strokes: number[] = []
  const ctx = new Proxy({}, {
    get: (_, name: string) => (name === 'stroke' ? () => strokes.push(1) : () => undefined),
    set: () => true,
  })
  return { ctx: ctx as unknown as CanvasRenderingContext2D, strokes }
}

describe('drawHoneycomb', () => {
  const colors = { line: 'green', fill: 'lime' }

  it('draws the grid in one stroke and strokes only the lit cells again', () => {
    const { ctx, strokes } = recorder()
    drawHoneycomb(ctx, colors, 1200, 800, 4)
    const lit = cellsFor(1200, 800).filter((_, index) => twinkleLevel(index, 4) >= 0.12)
    expect(strokes).toHaveLength(1 + lit.length)
    expect(lit.length).toBeLessThan(cellsFor(1200, 800).length)
  })

  it('draws at any time without error', () => {
    for (let time = 0; time < 120; time += 7.3) {
      const { ctx } = recorder()
      expect(() => drawHoneycomb(ctx, colors, 900, 600, time)).not.toThrow()
    }
  })
})

describe('the canvas', () => {
  it('is hidden from assistive technology', () => {
    const { container } = render(<Honeycomb animated={false} />)
    const canvas = container.querySelector('canvas')
    expect(canvas).toHaveAttribute('aria-hidden', 'true')
    expect(canvas).toHaveAttribute('data-animated', 'false')
  })

  it('says when it is animated', () => {
    const { container } = render(<Honeycomb animated />)
    expect(container.querySelector('canvas')).toHaveAttribute('data-animated', 'true')
  })
})

describe('the frame meter', () => {
  it('stays quiet while frames are cheap', () => {
    const meter = new FrameMeter()
    const verdicts = Array.from({ length: 60 }, () => meter.tooSlow(2))
    expect(verdicts.some(Boolean)).toBe(false)
  })

  it('says so once a batch of frames is too slow on average', () => {
    const meter = new FrameMeter()
    const verdicts = Array.from({ length: 30 }, () => meter.tooSlow(20))
    expect(verdicts.slice(0, 29).some(Boolean)).toBe(false)
    expect(verdicts[29]).toBe(true)
  })

  it('judges each batch on its own', () => {
    const meter = new FrameMeter()
    Array.from({ length: 30 }, () => meter.tooSlow(20))
    const next = Array.from({ length: 30 }, () => meter.tooSlow(2))
    expect(next.some(Boolean)).toBe(false)
  })
})
