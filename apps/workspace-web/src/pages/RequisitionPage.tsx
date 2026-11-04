import { useEffect, useState } from 'react'
import { Link, useParams, useRouteContext } from '@tanstack/react-router'
import { Alert, Button, Container, Group, Loader, Stack, Table, Text, TextInput, Title } from '@sami/ui'
import type { Requisition, RequisitionResult } from '../api/purchaseRequisitions'
import { canBeReleased, itemStatus, requisitionStatus } from '../requisitionStatus'
import { StatusBadge } from './StatusBadge'

const refusal = (result: Extract<RequisitionResult, { ok: false }>): string[] => {
  if (result.kind === 'validation') return result.details.map((detail) => detail.message)
  if (result.kind === 'unavailable') return ['SAP is not reachable. Try again in a moment.']
  if (result.kind === 'notFound' || result.kind === 'notAllowed') return ['You cannot release this requisition.']
  return ['Something went wrong. Try again.']
}

export function RequisitionPage() {
  const { number } = useParams({ from: '/purchase-requisitions/$number' })
  const { purchaseRequisitions, session } = useRouteContext({ from: '/purchase-requisitions/$number' })
  const [requisition, setRequisition] = useState<Requisition | null>(null)
  const [state, setState] = useState<'loading' | 'missing' | 'failed' | 'ready'>('loading')
  const [code, setCode] = useState('')
  const [messages, setMessages] = useState<string[]>([])
  const [pending, setPending] = useState(false)
  const isApprover = session.status === 'signedIn' && session.user.roles.includes('management')

  useEffect(() => {
    let current = true
    purchaseRequisitions.get(number).then(
      (found) => {
        if (!current) return
        setRequisition(found)
        setState(found === null ? 'missing' : 'ready')
      },
      () => current && setState('failed'),
    )
    return () => {
      current = false
    }
  }, [purchaseRequisitions, number])

  const release = async (item?: string) => {
    if (!code.trim()) {
      setMessages(['Enter the release code.'])
      return
    }
    setPending(true)
    setMessages([])
    const result = await purchaseRequisitions.release(number, code.trim(), item)
    setPending(false)
    if (result.ok) setRequisition(result.requisition)
    else setMessages(refusal(result))
  }

  if (state === 'loading') return <Loader />
  if (state === 'missing') return <Alert color="yellow">No such purchase requisition.</Alert>
  if (state === 'failed' || requisition === null) return <Alert color="red">Could not load the requisition.</Alert>

  const releasable = requisition.items.some(canBeReleased)
  return (
    <Container size="lg" py="md">
      <Stack>
        <Group justify="space-between">
          <Title order={2}>Requisition {requisition.purchase_requisition}</Title>
          <StatusBadge status={requisitionStatus(requisition)} />
        </Group>
        <Text>{requisition.description}</Text>
        <Text size="sm" c="dimmed">
          Created by {requisition.created_by_user}
          {requisition.created_on ? ` on ${requisition.created_on}` : ''}. Total {requisition.total_net_amount}
        </Text>
        {isApprover && releasable && (
          <Group align="flex-end">
            <TextInput label="Release code" value={code} onChange={(e) => setCode(e.currentTarget.value)} />
            <Button loading={pending} onClick={() => release()}>
              Release all
            </Button>
          </Group>
        )}
        {messages.length > 0 && (
          <Alert color="red">
            {messages.map((message) => (
              <div key={message}>{message}</div>
            ))}
          </Alert>
        )}
        <Table>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Item</Table.Th>
              <Table.Th>Material</Table.Th>
              <Table.Th>Plant</Table.Th>
              <Table.Th>Quantity</Table.Th>
              <Table.Th>Amount</Table.Th>
              <Table.Th>Delivery</Table.Th>
              <Table.Th>Status</Table.Th>
              {isApprover && <Table.Th />}
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {requisition.items.map((item) => (
              <Table.Tr key={item.item}>
                <Table.Td>{item.item}</Table.Td>
                <Table.Td>
                  {item.material}
                  {item.text ? ` ${item.text}` : ''}
                </Table.Td>
                <Table.Td>{item.plant}</Table.Td>
                <Table.Td>
                  {item.quantity} {item.unit}
                </Table.Td>
                <Table.Td>
                  {item.net_amount} {item.currency}
                </Table.Td>
                <Table.Td>{item.delivery_date}</Table.Td>
                <Table.Td>
                  <StatusBadge status={itemStatus(item)} />
                </Table.Td>
                {isApprover && (
                  <Table.Td>
                    {canBeReleased(item) && (
                      <Button variant="default" loading={pending} onClick={() => release(item.item)} aria-label={`Release item ${item.item}`}>
                        Release
                      </Button>
                    )}
                  </Table.Td>
                )}
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
        <Button component={Link} to="/purchase-requisitions" variant="default">
          Back to the list
        </Button>
      </Stack>
    </Container>
  )
}
