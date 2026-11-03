import { useCallback, useEffect, useState } from 'react'
import { useRouteContext } from '@tanstack/react-router'
import { Alert, Badge, Button, Container, Group, Loader, Select, Stack, Table, Text, TextInput, Title } from '@sami/ui'
import type { AdminUser } from '../api/adminClient'
import { companyLabel } from '../roles'
import { UserForm } from './UserForm'

const statusOptions = [
  { value: 'all', label: 'Any status' },
  { value: 'active', label: 'Active' },
  { value: 'disabled', label: 'Disabled' },
]

export function UsersPage() {
  const { admin, session } = useRouteContext({ from: '/users' })
  const [users, setUsers] = useState<AdminUser[] | null>(null)
  const [failed, setFailed] = useState(false)
  const [query, setQuery] = useState('')
  const [role, setRole] = useState<string | null>(null)
  const [status, setStatus] = useState('all')
  const [roles, setRoles] = useState<string[]>([])
  const [companies, setCompanies] = useState<string[]>([])
  const [editing, setEditing] = useState<AdminUser | 'new' | null>(null)

  const load = useCallback(async () => {
    try {
      setUsers(await admin.users(query))
      setFailed(false)
    } catch {
      setFailed(true)
    }
  }, [admin, query])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    admin.roles().then(setRoles)
    admin.companies().then(setCompanies)
  }, [admin])

  const shown = (users ?? []).filter((user) => (!role || user.roles.includes(role)) && (status === 'all' || (status === 'disabled') === user.disabled))
  const ownId = session.status === 'signedIn' ? session.user.userid : ''

  return (
    <Container size="xl" py="md">
      <Stack>
        <Group justify="space-between">
          <Title order={2}>Users</Title>
          <Button onClick={() => setEditing('new')}>New user</Button>
        </Group>
        <Group>
          <TextInput aria-label="Search users" placeholder="Search name or email" value={query} onChange={(event) => setQuery(event.currentTarget.value)} />
          <Select aria-label="Filter by role" placeholder="Any role" clearable data={roles} value={role} onChange={setRole} />
          <Select aria-label="Filter by status" allowDeselect={false} data={statusOptions} value={status} onChange={(value) => setStatus(value ?? 'all')} />
        </Group>
        {failed && <Alert color="red">The users could not be loaded.</Alert>}
        {!users && !failed && <Loader />}
        {users && (
          <Table highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Name</Table.Th>
                <Table.Th>Email</Table.Th>
                <Table.Th>SAP username</Table.Th>
                <Table.Th>Roles</Table.Th>
                <Table.Th>Companies</Table.Th>
                <Table.Th>Status</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {shown.map((user) => (
                <Table.Tr key={user.userid} style={{ cursor: 'pointer', opacity: user.disabled ? 0.55 : 1 }} onClick={() => setEditing(user)}>
                  <Table.Td>{user.fullname}</Table.Td>
                  <Table.Td>
                    {user.email} {!user.has_password && <Badge variant="light">Entra</Badge>}
                  </Table.Td>
                  <Table.Td>{user.sap_username}</Table.Td>
                  <Table.Td>
                    <Group gap={4}>
                      {user.roles.map((name) => (
                        <Badge key={name} variant="light">
                          {name}
                        </Badge>
                      ))}
                    </Group>
                  </Table.Td>
                  <Table.Td>{user.companies.map((name) => companyLabel[name] ?? name).join(', ')}</Table.Td>
                  <Table.Td>{user.disabled ? <Badge color="gray">Disabled</Badge> : <Badge color="green">Active</Badge>}</Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
        {users && shown.length === 0 && <Text c="dimmed">No users match.</Text>}
      </Stack>
      <UserForm
        opened={editing !== null}
        user={editing === 'new' ? null : editing}
        ownId={ownId}
        roles={roles}
        companies={companies}
        admin={admin}
        onClose={() => setEditing(null)}
        onSaved={() => {
          setEditing(null)
          load()
        }}
      />
    </Container>
  )
}
