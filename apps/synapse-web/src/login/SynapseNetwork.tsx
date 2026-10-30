import { chains, edges, nodes } from './network'
import classes from './SynapseNetwork.module.css'

const CYCLE = 12
const TRAVEL = 2.4
const STAGGER = 2

type SynapseNetworkProps = { animated: boolean }

export function SynapseNetwork({ animated }: SynapseNetworkProps) {
  return (
    <svg className={classes.network} viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">
      <defs>
        <filter id="synapse-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <g className={classes.lines}>
        {edges.map(([a, b]) => (
          <line key={`${a}-${b}`} x1={nodes[a].x} y1={nodes[a].y} x2={nodes[b].x} y2={nodes[b].y} />
        ))}
      </g>
      <g className={classes.nodes}>
        {nodes.map((node, index) => (
          <circle key={index} cx={node.x} cy={node.y} r={3.5} />
        ))}
      </g>
      {animated &&
        chains.map((chain, order) => {
          const begin = order * STAGGER
          return (
            <g key={order} data-testid="pulse" className={classes.pulse} filter="url(#synapse-glow)">
              <polyline points={chain.map((index) => `${nodes[index].x},${nodes[index].y}`).join(' ')} pathLength={100} strokeDasharray="7 100" strokeDashoffset={7}>
                <animate attributeName="stroke-dashoffset" values="7;-100;-100" keyTimes={`0;${TRAVEL / CYCLE};1`} dur={`${CYCLE}s`} begin={`${begin}s`} repeatCount="indefinite" />
              </polyline>
              {chain.map((index, step) => (
                <circle key={index} cx={nodes[index].x} cy={nodes[index].y} r={3.5} opacity={0}>
                  <animate
                    attributeName="opacity"
                    values="0;1;0;0"
                    keyTimes={`0;0.02;0.1;1`}
                    dur={`${CYCLE}s`}
                    begin={`${begin + (step / (chain.length - 1)) * TRAVEL * 0.9}s`}
                    repeatCount="indefinite"
                  />
                  <animate
                    attributeName="r"
                    values="3.5;9;3.5;3.5"
                    keyTimes={`0;0.02;0.1;1`}
                    dur={`${CYCLE}s`}
                    begin={`${begin + (step / (chain.length - 1)) * TRAVEL * 0.9}s`}
                    repeatCount="indefinite"
                  />
                </circle>
              ))}
            </g>
          )
        })}
    </svg>
  )
}
