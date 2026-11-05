import { useCallback, useState } from 'react'
import type { SyntheticEvent } from 'react'
import { useRouteContext } from '@tanstack/react-router'
import { Alert, Button, Container, Group, Stack, Text, TextInput, Title } from '@sami/ui'
import { RemoteSelect } from '../components/RemoteSelect'
import { addItem, fieldKey, initialForm, mapDetails, removeItem, toNewOrder } from '../orderForm'
import type { CustomerOption, FieldErrors, ItemForm, OrderForm } from '../orderForm'
import type { MaterialOption } from '../requisitionForm'
import { WaitingOrders } from './WaitingOrders'

type Notice = { color: 'green' | 'yellow' | 'red'; text: string }

const noErrors: FieldErrors = { fields: {}, general: [] }
const SOLD = 'FERT'

export function NewOrderPage() {
  const { salesOrders, masterData } = useRouteContext({ from: '/sales-orders/new' })
  const [form, setForm] = useState<OrderForm>(initialForm)
  const [errors, setErrors] = useState<FieldErrors>(noErrors)
  const [notice, setNotice] = useState<Notice | null>(null)
  const [pending, setPending] = useState(false)
  const [reloadKey, setReloadKey] = useState(0)

  const setHeader = (field: 'salesOrderType' | 'transactionCurrency' | 'requestedDeliveryDate', value: string) =>
    setForm({ ...form, [field]: value })

  const setItem = (index: number, changes: Partial<ItemForm>) =>
    setForm((now) => ({ ...now, items: now.items.map((item, i) => (i === index ? { ...item, ...changes } : item)) }))

  const searchCustomers = useCallback(
    async (query: string): Promise<CustomerOption[]> =>
      (await masterData.customers(query)).map((c) => ({ value: c.number, label: `${c.number} ${c.name}`, companyCode: c.company_codes[0] ?? '' })),
    [masterData],
  )

  const searchMaterials = useCallback(
    async (query: string): Promise<MaterialOption[]> =>
      (await masterData.materials(query))
        .filter((m) => m.material_type === SOLD)
        .map((m) => ({ value: m.material, label: `${m.material} ${m.description}`, unit: m.unit })),
    [masterData],
  )

  const submit = async (event: SyntheticEvent) => {
    event.preventDefault()
    setPending(true)
    setErrors(noErrors)
    setNotice(null)
    const result = await salesOrders.create(toNewOrder(form))
    setPending(false)
    if (result.ok) {
      setForm(initialForm())
      setNotice({ color: 'green', text: `Sales order ${result.salesOrder} created` })
    } else if (result.kind === 'queued' || result.kind === 'unknown') {
      setForm(initialForm())
      setReloadKey(reloadKey + 1)
      setNotice(
        result.kind === 'queued'
          ? { color: 'yellow', text: 'Saved. SAP could not take the order right now; it will be sent automatically.' }
          : {
              color: 'red',
              text: 'We could not confirm that SAP received the order. Do not enter it again; check with your SAP contact or the order list.',
            },
      )
    } else if (result.kind === 'validation') {
      setErrors(mapDetails(result.details, form.items.length))
    } else if (result.kind === 'notSaved') {
      setNotice({ color: 'red', text: 'The order could not be saved and nothing was sent. Try again.' })
    } else if (result.kind === 'unavailable') {
      setNotice({ color: 'red', text: 'SAP is not available. Try again in a moment.' })
    } else {
      setNotice({ color: 'red', text: 'Something went wrong. Try again.' })
    }
  }

  const headerInput = (label: string, field: 'salesOrderType' | 'transactionCurrency' | 'requestedDeliveryDate', type = 'text') => (
    <TextInput
      label={label}
      type={type}
      value={form[field]}
      error={errors.fields[field]}
      onChange={(e) => setHeader(field, e.currentTarget.value)}
    />
  )

  return (
    <Container size="sm" py="md">
      <form onSubmit={submit}>
        <Stack>
          <Title order={2}>New sales order</Title>
          {notice && <Alert color={notice.color}>{notice.text}</Alert>}
          {errors.general.length > 0 && (
            <Alert color="red">
              {errors.general.map((message) => (
                <div key={message}>{message}</div>
              ))}
            </Alert>
          )}
          {headerInput('Order type', 'salesOrderType')}
          <RemoteSelect
            label="Customer"
            search={searchCustomers}
            selected={form.customer}
            onSelect={(customer) => setForm({ ...form, customer })}
            error={errors.fields.customer}
          />
          {headerInput('Currency', 'transactionCurrency')}
          {headerInput('Requested delivery date', 'requestedDeliveryDate', 'date')}
          <Title order={4}>Items</Title>
          {form.items.map((item, index) => (
            <Group key={index} align="flex-start" grow>
              <RemoteSelect
                label="Material"
                search={searchMaterials}
                selected={item.material}
                onSelect={(material) => setItem(index, { material })}
                error={errors.fields[fieldKey(index, 'material')]}
              />
              <TextInput
                label="Quantity"
                value={item.quantity}
                error={errors.fields[fieldKey(index, 'quantity')]}
                rightSection={<Text size="sm">{item.material?.unit ?? ''}</Text>}
                rightSectionWidth={44}
                onChange={(e) => setItem(index, { quantity: e.currentTarget.value })}
              />
              {form.items.length > 1 && (
                <Button variant="default" onClick={() => setForm(removeItem(form, index))}>
                  Remove
                </Button>
              )}
            </Group>
          ))}
          <Group>
            <Button variant="default" onClick={() => setForm(addItem(form))}>
              Add item
            </Button>
            <Button type="submit" loading={pending}>
              Create order
            </Button>
          </Group>
        </Stack>
      </form>
      <WaitingOrders salesOrders={salesOrders} reloadKey={reloadKey} />
    </Container>
  )
}
