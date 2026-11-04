import { useEffect, useState } from 'react'
import { Link, useRouteContext } from '@tanstack/react-router'
import { Alert, Button, Container, Group, Loader, Pagination, Stack, Table, Text, Title } from '@sami/ui'
import type { RequisitionPage } from '../api/purchaseRequisitions'
import { requisitionStatus } from '../requisitionStatus'
import { StatusBadge } from './StatusBadge'

export const PAGE_SIZE = 20

export function RequisitionsPage() {
  const { purchaseRequisitions, session } = useRouteContext({ from: '/purchase-requisitions' })
  const [page, setPage] = useState(1)
  const [found, setFound] = useState<RequisitionPage | null>(null)
  const [failed, setFailed] = useState(false)
  const canCreate = session.status === 'signedIn' && session.user.roles.includes('purchase')

  useEffect(() => {
    let current = true
    purchaseRequisitions.list(PAGE_SIZE, (page - 1) * PAGE_SIZE).then(
      (result) => {
        if (!current) return
        setFound(result)
        setFailed(false)
      },
      () => current && setFailed(true),
    )
    return () => {
      current = false
    }
  }, [purchaseRequisitions, page])

  return (
    <Container size="lg" py="md">
      <Stack>
        <Group justify="space-between">
          <Title order={2}>Purchase requisitions</Title>
          {canCreate && (
            <Button component={Link} to="/purchase-requisitions/new">
              New requisition
            </Button>
          )}
        </Group>
        {failed && <Alert color="red">Could not load the requisitions. Try again in a moment.</Alert>}
        {!failed && found === null && <Loader />}
        {found !== null && found.requisitions.length === 0 && <Text c="dimmed">No purchase requisitions yet.</Text>}
        {found !== null && found.requisitions.length > 0 && (
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Number</Table.Th>
                <Table.Th>Description</Table.Th>
                <Table.Th>Items</Table.Th>
                <Table.Th>Total</Table.Th>
                <Table.Th>Created</Table.Th>
                <Table.Th>Status</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {found.requisitions.map((requisition) => (
                <Table.Tr key={requisition.purchase_requisition}>
                  <Table.Td>
                    <Link to="/purchase-requisitions/$number" params={{ number: requisition.purchase_requisition }}>
                      {requisition.purchase_requisition}
                    </Link>
                  </Table.Td>
                  <Table.Td>{requisition.description}</Table.Td>
                  <Table.Td>{requisition.items.length}</Table.Td>
                  <Table.Td>{requisition.total_net_amount}</Table.Td>
                  <Table.Td>{requisition.created_on ?? ''}</Table.Td>
                  <Table.Td>
                    <StatusBadge status={requisitionStatus(requisition)} />
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
        {found !== null && found.total > PAGE_SIZE && (
          <Pagination value={page} onChange={setPage} total={Math.ceil(found.total / PAGE_SIZE)} />
        )}
      </Stack>
    </Container>
  )
}
