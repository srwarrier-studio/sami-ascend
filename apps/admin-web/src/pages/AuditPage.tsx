import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useRouteContext, useSearch } from '@tanstack/react-router'
import { Alert, Badge, Button, Container, Group, Select, Stack, Switch, Table, Text, TextInput, Title, Tooltip } from '@sami/ui'
import type { AuditEntry, AuditFilters } from '../api/adminClient'
import { auditCsv } from '../csv'

export type AuditSearch = { actor?: string; action?: string; outcome?: string; from?: string; to?: string }

const PAGE = 50
const EXPORT_LIMIT = 5000
const EXPORT_PAGE = 200
const REFRESH_MS = 30_000

const ACTIONS = ['login.password', 'login.entra', 'user.create', 'user.update', 'user.disable', 'user.enable']

const dayStart = (date: string) => new Date(`${date}T00:00:00`).toISOString()
const dayEnd = (date: string) => new Date(`${date}T23:59:59.999`).toISOString()
const today = () => new Date().toLocaleDateString('en-CA')

export const toFilters = (search: AuditSearch): AuditFilters => ({
  actor: search.actor,
  action: search.action,
  outcome: search.outcome,
  from: search.from ? dayStart(search.from) : undefined,
  to: search.to ? dayEnd(search.to) : undefined,
})

const ago = (iso: string) => {
  const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min ago`
  if (minutes < 1440) return `${Math.round(minutes / 60)} h ago`
  return `${Math.round(minutes / 1440)} d ago`
}

const quickViews: { label: string; search: AuditSearch }[] = [
  { label: 'Failed sign-ins', search: { outcome: 'failed', action: 'login.*' } },
  { label: 'Admin changes', search: { action: 'user.*' } },
  { label: 'Today', search: {} },
]

export function AuditPage() {
  const { admin } = useRouteContext({ from: '/audit' })
  const search = useSearch({ from: '/audit' })
  const navigate = useNavigate({ from: '/audit' })
  const [rows, setRows] = useState<AuditEntry[]>([])
  const [next, setNext] = useState<number | null>(null)
  const [loadedAt, setLoadedAt] = useState<Date | null>(null)
  const [failed, setFailed] = useState(false)
  const [loaded, setLoaded] = useState(false)
  const [auto, setAuto] = useState(false)
  const [exporting, setExporting] = useState(false)
  const filtersKey = JSON.stringify(search)

  const load = useCallback(async () => {
    try {
      const page = await admin.audit(toFilters(JSON.parse(filtersKey)), null, PAGE)
      setRows(page.items)
      setNext(page.next)
      setLoadedAt(new Date())
      setFailed(false)
    } catch {
      setFailed(true)
    } finally {
      setLoaded(true)
    }
  }, [admin, filtersKey])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (!auto) return
    const timer = setInterval(load, REFRESH_MS)
    return () => clearInterval(timer)
  }, [auto, load])

  const more = async () => {
    if (next === null) return
    const page = await admin.audit(toFilters(search), next, PAGE)
    setRows((current) => [...current, ...page.items])
    setNext(page.next)
  }

  const change = (patch: AuditSearch) => navigate({ search: (current) => ({ ...current, ...patch }) })

  const exportCsv = async () => {
    setExporting(true)
    try {
      const all: AuditEntry[] = []
      let before: number | null = null
      do {
        const page = await admin.audit(toFilters(search), before, EXPORT_PAGE)
        all.push(...page.items)
        before = page.next
      } while (before !== null && all.length < EXPORT_LIMIT)
      const url = URL.createObjectURL(new Blob([auditCsv(all.slice(0, EXPORT_LIMIT))], { type: 'text/csv' }))
      const link = document.createElement('a')
      link.href = url
      link.download = `audit-log-${today()}.csv`
      link.click()
      URL.revokeObjectURL(url)
    } finally {
      setExporting(false)
    }
  }

  const applyQuick = (view: (typeof quickViews)[number]) =>
    navigate({ search: view.label === 'Today' ? { from: today(), to: today() } : view.search })

  return (
    <Container size="xl" py="md">
      <Stack>
        <Group justify="space-between">
          <Title order={2}>Audit log</Title>
          <Group>
            {loadedAt && <Text size="sm" c="dimmed">{`Loaded ${loadedAt.toLocaleTimeString()}`}</Text>}
            <Switch label="Auto-refresh" checked={auto} onChange={(event) => setAuto(event.currentTarget.checked)} />
            <Button variant="default" onClick={load}>
              Refresh
            </Button>
            <Button variant="default" loading={exporting} onClick={exportCsv}>
              Export CSV
            </Button>
          </Group>
        </Group>
        <Group>
          {quickViews.map((view) => (
            <Button key={view.label} size="xs" variant="light" onClick={() => applyQuick(view)}>
              {view.label}
            </Button>
          ))}
          <Button size="xs" variant="subtle" onClick={() => navigate({ search: {} })}>
            Clear filters
          </Button>
        </Group>
        <Group align="flex-end">
          <TextInput label="Actor" placeholder="email" value={search.actor ?? ''} onChange={(event) => change({ actor: event.currentTarget.value || undefined })} />
          <Select label="Action" placeholder="Any action" clearable data={ACTIONS} value={search.action && ACTIONS.includes(search.action) ? search.action : null} onChange={(value) => change({ action: value ?? undefined })} />
          <Select label="Outcome" placeholder="Any outcome" clearable data={['success', 'failed']} value={search.outcome ?? null} onChange={(value) => change({ outcome: value ?? undefined })} />
          <TextInput label="From" type="date" value={search.from ?? ''} onChange={(event) => change({ from: event.currentTarget.value || undefined })} />
          <TextInput label="To" type="date" value={search.to ?? ''} onChange={(event) => change({ to: event.currentTarget.value || undefined })} />
        </Group>
        {failed && <Alert color="red">The audit log could not be loaded.</Alert>}
        <Table highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Time</Table.Th>
              <Table.Th>Actor</Table.Th>
              <Table.Th>Action</Table.Th>
              <Table.Th>Target</Table.Th>
              <Table.Th>Outcome</Table.Th>
              <Table.Th>Detail</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {rows.map((row) => (
              <Table.Tr key={row.id}>
                <Table.Td>
                  <Tooltip label={ago(row.at)}>
                    <span>{new Date(row.at).toLocaleString()}</span>
                  </Tooltip>
                </Table.Td>
                <Table.Td>{row.actor}</Table.Td>
                <Table.Td>{row.action}</Table.Td>
                <Table.Td>{row.target}</Table.Td>
                <Table.Td>
                  <Badge color={row.outcome === 'success' ? 'green' : 'red'}>{row.outcome}</Badge>
                </Table.Td>
                <Table.Td>{row.detail}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
        {loaded && !failed && rows.length === 0 && <Text c="dimmed">Nothing in the log matches these filters.</Text>}
        {next !== null && (
          <Group justify="center">
            <Button variant="default" onClick={more}>
              Load more
            </Button>
          </Group>
        )}
      </Stack>
    </Container>
  )
}
