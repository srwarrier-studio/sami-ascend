import type { ReactNode } from 'react'
import { Link } from '@tanstack/react-router'
import { AppShell, Button, Group, NavLink, Text, Title } from '@sami/ui'
import type { User } from './api/auth'
import { WorkspaceLogo } from './brand/WorkspaceLogo'
import { APP_NAME } from './config'
import { allowedEntries } from './menu'

type ShellProps = { user: User; onLogout: () => void; children: ReactNode }

export function Shell({ user, onLogout, children }: ShellProps) {
  return (
    <AppShell header={{ height: 60 }} navbar={{ width: 240, breakpoint: 'sm' }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group gap="xs">
            <Group c="brand" gap={0}>
              <WorkspaceLogo size={28} />
            </Group>
            <Title order={4}>{APP_NAME}</Title>
          </Group>
          <Group>
            <Text>{user.sap_username}</Text>
            <Button variant="default" onClick={onLogout}>
              Sign out
            </Button>
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="md">
        <NavLink component={Link} to="/" label="Home" />
        {allowedEntries(user.roles).map((entry) => (
          <NavLink key={entry.path} component={Link} to={entry.path} label={entry.label} />
        ))}
      </AppShell.Navbar>
      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  )
}
