import { useId } from 'react'

const CHANNEL = 'M400 30 C210 190 590 290 400 400 C210 510 590 610 400 770'
const LEFT = 'M400 30 L79.6 215 L79.6 585 L400 770 C590 610 210 510 400 400 C590 290 210 190 400 30 Z'
const RIGHT = 'M400 30 L720.4 215 L720.4 585 L400 770 C590 610 210 510 400 400 C590 290 210 190 400 30 Z'

export function WorkspaceLogo({ size = 32 }: { size?: number }) {
  const mask = `logo-${useId().replace(/:/g, '')}`
  return (
    <svg width={size} height={size} viewBox="0 0 800 800" aria-hidden="true" focusable="false" fill="currentColor">
      <defs>
        <mask id={mask}>
          <rect width="800" height="800" fill="#fff" />
          <path d={CHANNEL} fill="none" stroke="#000" strokeWidth="30" strokeLinecap="round" />
          <circle cx="255" cy="240" r="40" fill="#000" />
          <circle cx="545" cy="560" r="62" fill="#000" />
        </mask>
      </defs>
      <g mask={`url(#${mask})`}>
        <path d={LEFT} stroke="currentColor" strokeWidth="30" strokeLinejoin="round" />
        <path d={RIGHT} stroke="currentColor" strokeWidth="30" strokeLinejoin="round" opacity="0.5" />
      </g>
      <circle cx="545" cy="560" r="40" />
    </svg>
  )
}
