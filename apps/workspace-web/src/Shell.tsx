import type { ReactNode } from 'react'
import { Link } from '@tanstack/react-router'
import { AppShell, Button, Group, NavLink, Text, Title } from '@sami/ui'
import type { User } from './api/auth'
import { allowedEntries } from './menu'

type ShellProps = { user: User; onLogout: () => void; children: ReactNode }

export function Shell({ user, onLogout, children }: ShellProps) {
  return (
    <AppShell header={{ height: 60 }} navbar={{ width: 240, breakpoint: 'sm' }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Title order={4}>Workspace</Title>
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
