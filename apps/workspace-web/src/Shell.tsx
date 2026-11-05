import type { ReactNode } from 'react'
import { Link, useRouterState } from '@tanstack/react-router'
import { AppFrame } from '@sami/ui'
import type { NavItem } from '@sami/ui'
import type { User } from './api/auth'
import { WorkspaceLogo } from './brand/WorkspaceLogo'
import { APP_NAME } from './config'
import { activePath, navEntries, roleLabel } from './navigation'
import type { NavEntry } from './navigation'

type ShellProps = { user: User; onLogout: () => void; children: ReactNode }

const navItem = (entry: NavEntry, active: boolean): NavItem => ({
  key: entry.key,
  label: entry.label,
  icon: entry.icon,
  active,
  render: ({ className, children }) => (
    <Link to={entry.path} className={className} data-active={active || undefined}>
      {children}
    </Link>
  ),
})

export function Shell({ user, onLogout, children }: ShellProps) {
  const current = useRouterState({ select: (state) => state.location.pathname })
  const entries = navEntries(user.roles)
  const active = activePath(entries, current)
  return (
    <AppFrame
      layout="side"
      themeToggle={false}
      search={false}
      brand={{ name: APP_NAME, subtitle: roleLabel(user.roles), logo: <WorkspaceLogo size={28} /> }}
      user={{ name: user.sap_username, email: '' }}
      onSignOut={onLogout}
      navGroups={[entries.map((entry) => navItem(entry, entry.path === active))]}
    >
      {children}
    </AppFrame>
  )
}
