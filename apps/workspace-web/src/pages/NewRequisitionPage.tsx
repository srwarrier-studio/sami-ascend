import { useState } from 'react'
import type { SyntheticEvent } from 'react'
import { useNavigate, useRouteContext } from '@tanstack/react-router'
import { Alert, Button, Container, Group, Stack, TextInput, Title } from '@sami/ui'
import { addItem, fieldKey, initialForm, mapDetails, removeItem, toNewRequisition } from '../requisitionForm'
import type { FieldErrors, RequisitionForm, RequisitionItemForm } from '../requisitionForm'

const noErrors: FieldErrors = { fields: {}, general: [] }

export function NewRequisitionPage() {
  const { purchaseRequisitions } = useRouteContext({ from: '/purchase-requisitions/new' })
  const navigate = useNavigate()
  const [form, setForm] = useState<RequisitionForm>(initialForm)
  const [errors, setErrors] = useState<FieldErrors>(noErrors)
  const [notice, setNotice] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  const setItem = (index: number, field: keyof RequisitionItemForm, value: string) =>
    setForm({ ...form, items: form.items.map((item, i) => (i === index ? { ...item, [field]: value } : item)) })

  const submit = async (event: SyntheticEvent) => {
    event.preventDefault()
    setPending(true)
    setErrors(noErrors)
    setNotice(null)
    const result = await purchaseRequisitions.create(toNewRequisition(form))
    setPending(false)
    if (result.ok) {
      await navigate({ to: '/purchase-requisitions/$number', params: { number: result.requisition.purchase_requisition } })
    } else if (result.kind === 'validation') {
      setErrors(mapDetails(result.details, form.items.length))
    } else if (result.kind === 'notAllowed') {
      setNotice('You cannot enter a requisition for that plant.')
    } else if (result.kind === 'unavailable') {
      setNotice('SAP is not reachable. Nothing was saved; try again in a moment.')
    } else {
      setNotice('Something went wrong. Nothing was saved; try again.')
    }
  }

  const itemInput = (index: number, label: string, field: keyof RequisitionItemForm, type = 'text') => (
    <TextInput
      label={label}
      type={type}
      value={form.items[index][field]}
      error={errors.fields[fieldKey(index, field)]}
      onChange={(e) => setItem(index, field, e.currentTarget.value)}
    />
  )

  return (
    <Container size="md" py="md">
      <form onSubmit={submit}>
        <Stack>
          <Title order={2}>New purchase requisition</Title>
          {notice && <Alert color="red">{notice}</Alert>}
          {errors.general.length > 0 && (
            <Alert color="red">
              {errors.general.map((message) => (
                <div key={message}>{message}</div>
              ))}
            </Alert>
          )}
          <TextInput
            label="Description"
            value={form.description}
            error={errors.fields.description}
            onChange={(e) => setForm({ ...form, description: e.currentTarget.value })}
          />
          <Title order={4}>Items</Title>
          {form.items.map((_, index) => (
            <Group key={index} align="flex-start" grow>
              {itemInput(index, 'Material', 'material')}
              {itemInput(index, 'Plant', 'plant')}
              {itemInput(index, 'Quantity', 'quantity')}
              {itemInput(index, 'Unit', 'unit')}
              {itemInput(index, 'Delivery date', 'deliveryDate', 'date')}
              {itemInput(index, 'Text', 'text')}
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
              Create requisition
            </Button>
          </Group>
        </Stack>
      </form>
    </Container>
  )
}
