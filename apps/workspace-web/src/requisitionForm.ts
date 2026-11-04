import type { ErrorDetail } from './api/salesOrders'
import type { NewRequisition } from './api/purchaseRequisitions'

export type RequisitionItemForm = {
  material: string
  plant: string
  quantity: string
  unit: string
  deliveryDate: string
  text: string
}

export type RequisitionForm = { description: string; items: RequisitionItemForm[] }

export const emptyItem = (): RequisitionItemForm => ({
  material: '',
  plant: '',
  quantity: '',
  unit: '',
  deliveryDate: '',
  text: '',
})

export const initialForm = (): RequisitionForm => ({ description: '', items: [emptyItem()] })

export const addItem = (form: RequisitionForm): RequisitionForm => ({ ...form, items: [...form.items, emptyItem()] })

export const removeItem = (form: RequisitionForm, index: number): RequisitionForm =>
  form.items.length === 1 ? form : { ...form, items: form.items.filter((_, i) => i !== index) }

export const toNewRequisition = (form: RequisitionForm): NewRequisition => ({
  description: form.description.trim(),
  items: form.items.map((item) => ({
    material: item.material.trim(),
    plant: item.plant.trim(),
    quantity: item.quantity.trim(),
    unit: item.unit.trim(),
    delivery_date: item.deliveryDate.trim(),
    ...(item.text.trim() ? { text: item.text.trim() } : {}),
  })),
})

const itemFields: Record<string, keyof RequisitionItemForm> = {
  material: 'material',
  plant: 'plant',
  quantity: 'quantity',
  unit: 'unit',
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
