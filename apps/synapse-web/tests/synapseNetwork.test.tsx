import { render, screen } from '@testing-library/react'
import { SynapseNetwork } from '../src/login/SynapseNetwork'
import { chains, edges, nodes } from '../src/login/network'

describe('the network layout', () => {
  it('has about two dozen nodes, all joined to the network', () => {
    expect(nodes.length).toBe(24)
    nodes.forEach((_, index) => expect(edges.some(([a, b]) => a === index || b === index)).toBe(true))
  })

  it('walks every pulse along existing lines', () => {
    chains.forEach((chain) => {
      expect(chain.length).toBeGreaterThan(2)
      chain.slice(1).forEach((to, i) => {
        const from = chain[i]
        expect(edges.some(([a, b]) => (a === from && b === to) || (a === to && b === from))).toBe(true)
      })
    })
  })
})

describe('the network drawing', () => {
  it('draws the nodes and lines and hides them from assistive technology', () => {
    const { container } = render(<SynapseNetwork animated={false} />)
    expect(container.querySelector('svg')).toHaveAttribute('aria-hidden', 'true')
    expect(container.querySelectorAll('circle')).toHaveLength(nodes.length)
    expect(container.querySelectorAll('line')).toHaveLength(edges.length)
  })

  it('renders the pulses only when animated', () => {
    const { rerender } = render(<SynapseNetwork animated />)
    expect(screen.getAllByTestId('pulse')).toHaveLength(chains.length)
    rerender(<SynapseNetwork animated={false} />)
    expect(screen.queryAllByTestId('pulse')).toHaveLength(0)
  })
})
