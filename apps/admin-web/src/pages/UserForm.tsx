import { useEffect, useState } from 'react'
import { Alert, Button, Group, Modal, MultiSelect, PasswordInput, Stack, Text, TextInput } from '@sami/ui'
import { AdminError } from '../api/adminClient'
import type { AdminClient, AdminUser } from '../api/adminClient'
import { companyLabel, roleHelp } from '../roles'

type UserFormProps = {
  opened: boolean
  user: AdminUser | null
  ownId: string
  roles: string[]
  companies: string[]
  admin: AdminClient
  onClose: () => void
  onSaved: () => void
}

const messages: Record<string, string> = {
  USER_ALREADY_EXISTS: 'A user with this email already exists.',
  WEAK_PASSWORD: 'The password must be at least 12 characters.',
  LAST_ADMIN: 'At least one active admin is needed.',
  SELF_LOCKOUT: 'You cannot disable yourself or remove your own admin role.',
  ENTRA_USERNAME_TAKEN: 'That Entra username belongs to another user.',
}

const blank = { email: '', fullname: '', sap_username: '', entra_username: '', roles: [] as string[], companies: [] as string[], password: '' }

export function UserForm({ opened, user, ownId, roles, companies, admin, onClose, onSaved }: UserFormProps) {
  const [form, setForm] = useState(blank)
  const [error, setError] = useState('')
  const [confirming, setConfirming] = useState(false)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!opened) return
    setError('')
    setConfirming(false)
    setForm(user ? { ...blank, email: user.email, fullname: user.fullname, sap_username: user.sap_username, entra_username: user.entra_username ?? '', roles: user.roles, companies: user.companies } : blank)
  }, [opened, user])

  const set = (patch: Partial<typeof blank>) => setForm((current) => ({ ...current, ...patch }))

  const run = async (action: () => Promise<unknown>) => {
    setBusy(true)
    setError('')
    try {
      await action()
      onSaved()
    } catch (caught) {
      setError(caught instanceof AdminError ? (messages[caught.code] ?? caught.message) : 'The request failed.')
    } finally {
      setBusy(false)
    }
  }

  const save = () =>
    run(() =>
      user
        ? admin.updateUser(user.userid, { fullname: form.fullname, sap_username: form.sap_username, entra_username: form.entra_username, roles: form.roles, companies: form.companies })
        : admin.createUser({ ...form, entra_username: form.entra_username || null }),
    )

  const ready = form.fullname.trim() && form.sap_username.trim() && (user || form.email.includes('@'))
  const helped = form.roles.filter((role) => roleHelp[role])

  return (
    <Modal opened={opened} onClose={onClose} title={user ? `Edit ${user.fullname}` : 'New user'} size="lg">
      <Stack>
        <Text size="sm" c="dimmed">
          Entra proves who they are. What they can open is set here.
        </Text>
        {error && <Alert color="red">{error}</Alert>}
        <TextInput label="Name" value={form.fullname} onChange={(event) => set({ fullname: event.currentTarget.value })} />
        <TextInput label="Email" disabled={!!user} value={form.email} onChange={(event) => set({ email: event.currentTarget.value })} />
        <TextInput label="SAP username" value={form.sap_username} onChange={(event) => set({ sap_username: event.currentTarget.value })} />
        <TextInput label="Entra username" description="Only when it differs from the email" value={form.entra_username} onChange={(event) => set({ entra_username: event.currentTarget.value })} />
        <MultiSelect label="Roles" data={roles} value={form.roles} onChange={(value) => set({ roles: value })} />
        {helped.map((role) => (
          <Text key={role} size="xs" c="dimmed">
            {`${role}: ${roleHelp[role]}`}
          </Text>
        ))}
        <MultiSelect label="Companies" data={companies.map((value) => ({ value, label: companyLabel[value] ?? value }))} value={form.companies} onChange={(value) => set({ companies: value })} />
        {!user && <PasswordInput label="Password" description="Leave empty for Entra-only users" value={form.password} onChange={(event) => set({ password: event.currentTarget.value })} />}
        {confirming && user && (
          <Alert color="red" title={user.disabled ? `Enable ${user.fullname}?` : `Disable ${user.fullname}?`}>
            <Group mt="xs">
              <Button color="red" loading={busy} onClick={() => run(() => admin.updateUser(user.userid, { disabled: !user.disabled }))}>
                {user.disabled ? 'Yes, enable' : 'Yes, disable'}
              </Button>
              <Button variant="default" onClick={() => setConfirming(false)}>
                Keep as is
              </Button>
            </Group>
          </Alert>
        )}
        <Group justify="space-between">
          {user && user.userid !== ownId ? (
            <Button variant="subtle" color={user.disabled ? undefined : 'red'} onClick={() => setConfirming(true)}>
              {user.disabled ? 'Enable' : 'Disable'}
            </Button>
          ) : (
            <span />
          )}
          <Group>
            <Button variant="default" onClick={onClose}>
              Cancel
            </Button>
            <Button disabled={!ready} loading={busy} onClick={save}>
              {user ? 'Save' : 'Create user'}
            </Button>
          </Group>
        </Group>
      </Stack>
    </Modal>
  )
}
