import type { ErrorDetail, NewOrder } from './api/salesOrders'

export type ItemForm = { material: string; quantity: string; quantityUnit: string }

export type OrderForm = {
  salesOrderType: string
  soldToParty: string
  transactionCurrency: string
  requestedDeliveryDate: string
  items: ItemForm[]
}

export const emptyItem = (): ItemForm => ({ material: '', quantity: '', quantityUnit: '' })

export const initialForm = (): OrderForm => ({
  salesOrderType: 'OR',
  soldToParty: '',
  transactionCurrency: 'INR',
  requestedDeliveryDate: '',
  items: [emptyItem()],
})

export const addItem = (form: OrderForm): OrderForm => ({ ...form, items: [...form.items, emptyItem()] })

export const removeItem = (form: OrderForm, index: number): OrderForm =>
  form.items.length === 1 ? form : { ...form, items: form.items.filter((_, i) => i !== index) }

export const toNewOrder = (form: OrderForm): NewOrder => ({
  sales_order_type: form.salesOrderType.trim(),
  sold_to_party: form.soldToParty.trim(),
  transaction_currency: form.transactionCurrency.trim(),
  requested_delivery_date: form.requestedDeliveryDate.trim() || null,
  items: form.items.map((item) => ({
    material: item.material.trim(),
    quantity: item.quantity.trim(),
    quantity_unit: item.quantityUnit.trim(),
  })),
})

const headerFields: Record<string, string> = {
  SalesOrderType: 'salesOrderType',
  SoldToParty: 'soldToParty',
  TransactionCurrency: 'transactionCurrency',
  RequestedDeliveryDate: 'requestedDeliveryDate',
}

const itemFields: Record<string, string> = {
  Material: 'material',
  Quantity: 'quantity',
  QuantityUnit: 'quantityUnit',
}

export type FieldErrors = { fields: Record<string, string>; general: string[] }

export const fieldKey = (index: number, field: string) => `items.${index}.${field}`

export const mapDetails = (details: ErrorDetail[], itemCount: number): FieldErrors => {
  const result: FieldErrors = { fields: {}, general: [] }
  for (const detail of details) {
    const match = /^_Item\/(\d+)\/(\w+)$/.exec(detail.target)
    const key = match
      ? itemFields[match[2]] && Number(match[1]) < itemCount
        ? fieldKey(Number(match[1]), itemFields[match[2]])
        : undefined
      : headerFields[detail.target]
    if (key && !result.fields[key]) result.fields[key] = detail.message
    else result.general.push(detail.message)
  }
  return result
}
