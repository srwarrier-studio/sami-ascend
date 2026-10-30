import type { ReactNode } from 'react'
import { Link, useRouterState } from '@tanstack/react-router'
import { AppFrame, Button, CaretUpDownIcon, Group, Text, SquaresFourIcon, ChartBarIcon } from '@sami/ui'
import type { NavItem } from '@sami/ui'
import { CompanyLogo } from './session/CompanyLogo'
import { findCompany } from './session/companies'
import type { User } from './session/sessionClient'

type ShellProps = { user: User; company: string | null; onLogout: () => void; children: ReactNode }

const navItem = (key: string, label: string, icon: NavItem['icon'], to: '/' | '/reports', current: string): NavItem => ({
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

export function Shell({ user, company, onLogout, children }: ShellProps) {
  const current = useRouterState({ select: (state) => state.location.pathname })
  return (
    <AppFrame
      layout="top"
      themeToggle={false}
      brand={{ name: 'Synapse', subtitle: 'Management' }}
      user={{ name: user.name, email: user.email }}
      onSignOut={onLogout}
      search={false}
      headerExtra={
        company &&
        (user.companies.length > 1 ? (
          <Button
            component={Link}
            to="/company"
            aria-label="Switch company"
            variant="subtle"
            color="gray"
            radius="xl"
            size="md"
            leftSection={<CompanyLogo id={company} size={26} />}
            rightSection={<CaretUpDownIcon size={14} />}
          >
            {findCompany(company)?.name}
          </Button>
        ) : (
          <Group gap="xs" wrap="nowrap">
            <CompanyLogo id={company} size={26} />
            <Text size="sm" fw={500}>
              {findCompany(company)?.name}
            </Text>
          </Group>
        ))
      }
      navGroups={[
        [
          navItem('boards', 'My boards', SquaresFourIcon, '/', current),
          navItem('reports', 'Reports', ChartBarIcon, '/reports', current),
        ],
      ]}
    >
      {children}
    </AppFrame>
  )
}
