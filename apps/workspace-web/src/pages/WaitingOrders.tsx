import { useEffect, useState } from 'react'
import { Card, Stack, Table, Text, Title } from '@sami/ui'
import type { OrderRequest, SalesOrderClient } from '../api/salesOrders'

export const REFRESH_MS = 15000

const labels: Record<string, string> = {
  queued: 'Will be sent automatically',
  sending: 'Sending',
  unknown: 'Check in SAP',
  failed: 'Could not be sent',
}

const statusText = (request: OrderRequest) =>
  request.attempts > 0
    ? `${labels[request.status] ?? request.status}, tried ${request.attempts} ${request.attempts === 1 ? 'time' : 'times'}`
    : (labels[request.status] ?? request.status)

type Props = { salesOrders: SalesOrderClient; reloadKey: number }

export function WaitingOrders({ salesOrders, reloadKey }: Props) {
  const [orders, setOrders] = useState<OrderRequest[]>([])
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let current = true
    const load = () =>
      salesOrders.openRequests().then(
        (found) => {
          if (!current) return
          setOrders(found)
          setFailed(false)
        },
        () => current && setFailed(true),
      )
    load()
    const timer = setInterval(load, REFRESH_MS)
    return () => {
      current = false
      clearInterval(timer)
    }
  }, [salesOrders, reloadKey])

  if (failed) return <Text size="xs" c="dimmed">Could not load waiting orders</Text>
  if (orders.length === 0) return null
  return (
    <Card withBorder>
      <Stack>
        <Title order={4}>Waiting for SAP</Title>
        <Table>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Entered</Table.Th>
              <Table.Th>Customer</Table.Th>
              <Table.Th>Items</Table.Th>
              <Table.Th>Status</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {orders.map((request) => (
              <Table.Tr key={request.id}>
                <Table.Td>{new Date(request.created_at).toLocaleString()}</Table.Td>
                <Table.Td>{request.order.sold_to_party}</Table.Td>
                <Table.Td>{request.order.items.length}</Table.Td>
                <Table.Td>{statusText(request)}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Stack>
    </Card>
  )
}
