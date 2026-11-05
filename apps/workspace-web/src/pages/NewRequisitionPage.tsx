import { useCallback, useEffect, useState } from 'react'
import type { SyntheticEvent } from 'react'
import { useNavigate, useRouteContext } from '@tanstack/react-router'
import { Alert, Button, Container, Group, Select, Stack, Text, TextInput, Title } from '@sami/ui'
import type { Plant } from '../api/masterData'
import { RemoteSelect } from '../components/RemoteSelect'
import { addItem, fieldKey, initialForm, mapDetails, removeItem, toNewRequisition } from '../requisitionForm'
import type { FieldErrors, MaterialOption, RequisitionForm, RequisitionItemForm } from '../requisitionForm'

const noErrors: FieldErrors = { fields: {}, general: [] }

export function NewRequisitionPage() {
  const { purchaseRequisitions, masterData } = useRouteContext({ from: '/purchase-requisitions/new' })
  const navigate = useNavigate()
  const [form, setForm] = useState<RequisitionForm>(initialForm)
  const [errors, setErrors] = useState<FieldErrors>(noErrors)
  const [notice, setNotice] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const [plants, setPlants] = useState<Plant[]>([])
  const [plantsFailed, setPlantsFailed] = useState(false)

  useEffect(() => {
    let current = true
    masterData.plants().then(
      (found) => {
        if (!current) return
        setPlants(found)
        if (found.length === 1) setForm((now) => (now.items.some((i) => i.plant) ? now : initialForm(found[0].plant)))
      },
      () => current && setPlantsFailed(true),
    )
    return () => {
      current = false
    }
  }, [masterData])

  const setItem = (index: number, changes: Partial<RequisitionItemForm>) =>
    setForm((now) => ({ ...now, items: now.items.map((item, i) => (i === index ? { ...item, ...changes } : item)) }))

  const searchMaterials = useCallback(
    (plant: string) => async (query: string): Promise<MaterialOption[]> =>
      (await masterData.materials(query, plant)).map((m) => ({ value: m.material, label: `${m.material} ${m.description}`, unit: m.unit })),
    [masterData],
  )

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

  const plantOptions = plants.map((plant) => ({ value: plant.plant, label: `${plant.plant} ${plant.name}` }))

  return (
    <Container size="md" py="md">
      <form onSubmit={submit}>
        <Stack>
          <Title order={2}>New purchase requisition</Title>
          {notice && <Alert color="red">{notice}</Alert>}
          {plantsFailed && <Alert color="red">Could not load your plants. Reload the page to try again.</Alert>}
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
          {form.items.map((item, index) => (
            <Group key={index} align="flex-start" grow>
              <Select
                label="Plant"
                data={plantOptions}
                value={item.plant || null}
                error={errors.fields[fieldKey(index, 'plant')]}
                comboboxProps={{ withinPortal: false }}
                allowDeselect={false}
                onChange={(value) => setItem(index, { plant: value ?? '', material: null })}
              />
              <RemoteSelect
                label="Material"
                search={searchMaterials(item.plant)}
                selected={item.material}
                onSelect={(material) => setItem(index, { material })}
                disabled={!item.plant}
                resetKey={item.plant}
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
              <TextInput
                label="Delivery date"
                type="date"
                value={item.deliveryDate}
                error={errors.fields[fieldKey(index, 'deliveryDate')]}
                onChange={(e) => setItem(index, { deliveryDate: e.currentTarget.value })}
              />
              <TextInput label="Text" value={item.text} error={errors.fields[fieldKey(index, 'text')]} onChange={(e) => setItem(index, { text: e.currentTarget.value })} />
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
