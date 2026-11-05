import type { ErrorDetail } from './api/salesOrders'
import type { NewRequisition } from './api/purchaseRequisitions'
import type { RemoteOption } from './components/RemoteSelect'

export type MaterialOption = RemoteOption & { unit: string }

export type RequisitionItemForm = {
  plant: string
  material: MaterialOption | null
  quantity: string
  deliveryDate: string
  text: string
}

export type RequisitionForm = { description: string; items: RequisitionItemForm[] }

export const emptyItem = (plant = ''): RequisitionItemForm => ({
  plant,
  material: null,
  quantity: '',
  deliveryDate: '',
  text: '',
})

export const initialForm = (plant = ''): RequisitionForm => ({ description: '', items: [emptyItem(plant)] })

export const addItem = (form: RequisitionForm): RequisitionForm => ({
  ...form,
  items: [...form.items, emptyItem(form.items[form.items.length - 1]?.plant ?? '')],
})

export const removeItem = (form: RequisitionForm, index: number): RequisitionForm =>
  form.items.length === 1 ? form : { ...form, items: form.items.filter((_, i) => i !== index) }

export const toNewRequisition = (form: RequisitionForm): NewRequisition => ({
  description: form.description.trim(),
  items: form.items.map((item) => ({
    material: item.material?.value ?? '',
    plant: item.plant.trim(),
    quantity: item.quantity.trim(),
    unit: item.material?.unit ?? '',
    delivery_date: item.deliveryDate.trim(),
    ...(item.text.trim() ? { text: item.text.trim() } : {}),
  })),
})

const itemFields: Record<string, string> = {
  material: 'material',
  unit: 'material',
  plant: 'plant',
  quantity: 'quantity',
  delivery_date: 'deliveryDate',
  text: 'text',
}

export type FieldErrors = { fields: Record<string, string>; general: string[] }

export const fieldKey = (index: number, field: string) => `items.${index}.${field}`

export const mapDetails = (details: ErrorDetail[], itemCount: number): FieldErrors => {
  const result: FieldErrors = { fields: {}, general: [] }
  for (const detail of details) {
    const match = /^items\/(\d+)\/(\w+)$/.exec(detail.target)
    const key =
      match && itemFields[match[2]] && Number(match[1]) < itemCount
        ? fieldKey(Number(match[1]), itemFields[match[2]])
        : detail.target === 'description'
          ? 'description'
          : undefined
    if (key && !result.fields[key]) result.fields[key] = detail.message
    else result.general.push(detail.message)
  }
  return result
}
