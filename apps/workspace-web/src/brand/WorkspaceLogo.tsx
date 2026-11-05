export function WorkspaceLogo({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" focusable="false" fill="currentColor">
      <rect x="3" y="3" width="11" height="11" rx="3" />
      <rect x="18" y="3" width="11" height="11" rx="3" opacity="0.55" />
      <rect x="3" y="18" width="11" height="11" rx="3" opacity="0.55" />
      <rect x="18" y="18" width="11" height="11" rx="3" />
    </svg>
  )
}
