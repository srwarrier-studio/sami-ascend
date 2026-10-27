import { useState } from 'react'
import type { SyntheticEvent } from 'react'
import { useRouteContext } from '@tanstack/react-router'
import { Alert, Button, Container, Group, Stack, TextInput, Title } from '@sami/ui'
import {
  addItem,
  fieldKey,
  initialForm,
  mapDetails,
  removeItem,
  toNewOrder,
} from '../orderForm'
import type { FieldErrors, ItemForm, OrderForm } from '../orderForm'

type Notice = { color: 'green' | 'red'; text: string }

const noErrors: FieldErrors = { fields: {}, general: [] }

export function NewOrderPage() {
  const { salesOrders } = useRouteContext({ from: '/sales-orders/new' })
  const [form, setForm] = useState<OrderForm>(initialForm)
  const [errors, setErrors] = useState<FieldErrors>(noErrors)
  const [notice, setNotice] = useState<Notice | null>(null)
  const [pending, setPending] = useState(false)

  const setHeader = (field: keyof Omit<OrderForm, 'items'>, value: string) =>
    setForm({ ...form, [field]: value })

  const setItem = (index: number, field: keyof ItemForm, value: string) =>
    setForm({
      ...form,
      items: form.items.map((item, i) => (i === index ? { ...item, [field]: value } : item)),
    })

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
    } else if (result.kind === 'validation') {
      setErrors(mapDetails(result.details, form.items.length))
    } else if (result.kind === 'unavailable') {
      setNotice({ color: 'red', text: 'SAP is not available. Try again in a moment.' })
    } else {
      setNotice({ color: 'red', text: 'Something went wrong. Try again.' })
    }
  }

  const headerInput = (label: string, field: keyof Omit<OrderForm, 'items'>, type = 'text') => (
    <TextInput
      label={label}
      type={type}
      value={form[field]}
      error={errors.fields[field]}
      onChange={(e) => setHeader(field, e.currentTarget.value)}
    />
  )

  const itemInput = (index: number, label: string, field: keyof ItemForm) => (
    <TextInput
      label={label}
      value={form.items[index][field]}
      error={errors.fields[fieldKey(index, field)]}
      onChange={(e) => setItem(index, field, e.currentTarget.value)}
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
          {headerInput('Customer number', 'soldToParty')}
          {headerInput('Currency', 'transactionCurrency')}
          {headerInput('Requested delivery date', 'requestedDeliveryDate', 'date')}
          <Title order={4}>Items</Title>
          {form.items.map((_, index) => (
            <Group key={index} align="flex-start" grow>
              {itemInput(index, 'Material', 'material')}
              {itemInput(index, 'Quantity', 'quantity')}
              {itemInput(index, 'Unit', 'quantityUnit')}
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
    </Container>
  )
}
