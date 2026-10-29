import type { ReactNode } from 'react'
import { Link, useRouterState } from '@tanstack/react-router'
import { AppFrame, SquaresFourIcon, ChartBarIcon } from '@sami/ui'
import type { NavItem } from '@sami/ui'
import type { User } from './session/sessionClient'

type ShellProps = { user: User; onLogout: () => void; children: ReactNode }

const navItem = (key: string, label: string, icon: NavItem['icon'], to: '/' | '/widgets', current: string): NavItem => ({
  key,
  label,
  icon,
  active: current === to,
  render: ({ className, children }) => (
    <Link to={to} className={className} data-active={current === to || undefined}>
      {children}
    </Link>
  ),
})

export function Shell({ user, onLogout, children }: ShellProps) {
  const current = useRouterState({ select: (state) => state.location.pathname })
  return (
    <AppFrame
      layout="top"
      brand={{ name: 'Synapse', subtitle: 'Management' }}
      user={{ name: user.name, email: user.email }}
      onSignOut={onLogout}
      navGroups={[
        [
          navItem('boards', 'My boards', SquaresFourIcon, '/', current),
          navItem('widgets', 'Widgets', ChartBarIcon, '/widgets', current),
        ],
      ]}
    >
      {children}
    </AppFrame>
  )
}
