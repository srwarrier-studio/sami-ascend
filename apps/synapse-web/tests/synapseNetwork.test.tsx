import { render } from '@testing-library/react'
import { SynapseNetwork } from '../src/login/SynapseNetwork'
import { cascades, neurons, somas } from '../src/login/network'
import { CYCLE, TRAVEL, drift, DRIFT, flashLevel, hopsFrom, pulseProgress } from '../src/login/timeline'

describe('the neuron layout', () => {
  it('has seven neurons, each with branching dendrites', () => {
    expect(neurons).toHaveLength(7)
    neurons.forEach((neuron) => {
      expect(neuron.trunks).toContain('M')
      expect(neuron.twigs).toContain('M')
      expect(neuron.tips.length).toBeGreaterThan(5)
    })
  })

  it('reaches each axon to a terminal just before the next neuron', () => {
    neurons.slice(0, -1).forEach((neuron, index) => {
      const next = somas[index + 1]
      expect(neuron.axon).not.toBeNull()
      expect(neuron.axonLength).toBeGreaterThan(50)
      expect(Math.hypot(neuron.terminal!.x - next.x, neuron.terminal!.y - next.y)).toBeLessThan(50)
    })
    expect(neurons[neurons.length - 1].axon).toBeNull()
  })

  it('sends signals only along neurons that have an axon', () => {
    cascades.flat().forEach((index) => expect(neurons[index].axon).not.toBeNull())
  })
})

describe('the timeline', () => {
  it('moves a pulse from 0 to 1 while travelling and rests after', () => {
    expect(pulseProgress(0, 0)).toBe(0)
    expect(pulseProgress(TRAVEL / 2, 0)).toBeCloseTo(0.5)
    expect(pulseProgress(TRAVEL + 0.1, 0)).toBeNull()
  })

  it('repeats every cycle', () => {
    expect(pulseProgress(CYCLE + TRAVEL / 2, 0)).toBeCloseTo(0.5)
    expect(pulseProgress(1, 2)).toBeNull()
  })

  it('flashes up then fades out', () => {
    expect(flashLevel(0, 0)).toBe(0)
    expect(flashLevel(CYCLE * 0.02, 0)).toBeCloseTo(1)
    expect(flashLevel(CYCLE * 0.07, 0)).toBeCloseTo(0.5)
    expect(flashLevel(CYCLE * 0.5, 0)).toBe(0)
  })

  it('starts a hop for every cascade a neuron is in', () => {
    expect(hopsFrom(0)).toHaveLength(1)
    expect(hopsFrom(3)).toHaveLength(2)
    expect(hopsFrom(6)).toHaveLength(0)
  })

  it('keeps the drift small', () => {
    for (let time = 0; time < 100; time += 3) {
      const move = drift(2, time)
      expect(Math.abs(move.x)).toBeLessThanOrEqual(DRIFT)
      expect(Math.abs(move.y)).toBeLessThanOrEqual(DRIFT)
    }
  })
})

describe('the network drawing', () => {
  it('is a canvas hidden from assistive technology', () => {
    const { container } = render(<SynapseNetwork animated={false} />)
    const canvas = container.querySelector('canvas')
    expect(canvas).toHaveAttribute('aria-hidden', 'true')
    expect(canvas).toHaveAttribute('data-animated', 'false')
  })

  it('says when it is animated', () => {
    const { container } = render(<SynapseNetwork animated />)
    expect(container.querySelector('canvas')).toHaveAttribute('data-animated', 'true')
  })
})
