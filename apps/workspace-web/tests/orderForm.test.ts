import { addItem, emptyItem, fieldKey, initialForm, mapDetails, removeItem, toNewOrder } from '../src/orderForm'

const customer = { value: ' 0000100001 ', label: '0000100001 Harborline', companyCode: 'INA1' }
const steel = { value: ' RM-1001 ', label: 'RM-1001 Steel', unit: 'KG' }

describe('initial form', () => {
  it('has type OR, currency INR, no customer and one empty item', () => {
    const form = initialForm()
    expect(form).toMatchObject({ salesOrderType: 'OR', transactionCurrency: 'INR', customer: null })
    expect(form.items).toEqual([emptyItem()])
  })
})

describe('items', () => {
  it('adds a row', () => {
    expect(addItem(initialForm()).items).toHaveLength(2)
  })

  it('removes the chosen row', () => {
    let form = addItem(initialForm())
    form = { ...form, items: [{ ...form.items[0], quantity: 'A' }, { ...form.items[1], quantity: 'B' }] }
    expect(removeItem(form, 0).items.map((i) => i.quantity)).toEqual(['B'])
  })

  it('keeps the last row', () => {
    expect(removeItem(initialForm(), 0).items).toHaveLength(1)
  })
})

describe('toNewOrder', () => {
  it('sends the chosen customer, its company and the material with its unit', () => {
    const form = { ...initialForm(), customer, items: [{ material: steel, quantity: ' 5.5 ' }] }
    expect(toNewOrder(form)).toEqual({
      sales_order_type: 'OR',
      sold_to_party: ' 0000100001 ',
      company_code: 'INA1',
      transaction_currency: 'INR',
      requested_delivery_date: null,
      items: [{ material: ' RM-1001 ', quantity: '5.5', quantity_unit: 'KG' }],
    })
  })

  it('sends empty values when nothing was chosen, so SAP names the field', () => {
    expect(toNewOrder(initialForm())).toMatchObject({ sold_to_party: '', company_code: '', items: [{ material: '', quantity: '', quantity_unit: '' }] })
  })

  it('keeps a typed date', () => {
    expect(toNewOrder({ ...initialForm(), requestedDeliveryDate: '2026-11-05' }).requested_delivery_date).toBe('2026-11-05')
  })
})

describe('mapDetails', () => {
  const detail = (target: string, message = 'bad') => ({ code: 'X', target, message })

  it('puts customer and company refusals under the customer', () => {
    expect(mapDetails([detail('SoldToParty', 'Unknown customer')], 1).fields).toEqual({ customer: 'Unknown customer' })
    expect(mapDetails([detail('CompanyCode', 'Not yours')], 1).fields).toEqual({ customer: 'Not yours' })
  })

  it('maps item targets by row, a unit refusal under the material', () => {
    const result = mapDetails([detail('_Item/1/Quantity', 'Must be positive'), detail('_Item/0/QuantityUnit', 'Wrong unit'), detail('_Item/0/Material', 'No material')], 2)
    expect(result.fields).toEqual({ [fieldKey(1, 'quantity')]: 'Must be positive', [fieldKey(0, 'material')]: 'Wrong unit' })
    expect(result.general).toEqual(['No material'])
  })

  it('sends unmatched targets to general', () => {
    const result = mapDetails([detail('', 'Add an item'), detail('_Item/5/Quantity', 'gone'), detail('Other')], 1)
    expect(result.fields).toEqual({})
    expect(result.general).toEqual(['Add an item', 'gone', 'bad'])
  })

  it('keeps the first message when a field has two', () => {
    const result = mapDetails([detail('SoldToParty', 'first'), detail('SoldToParty', 'second')], 1)
    expect(result.fields.customer).toBe('first')
    expect(result.general).toEqual(['second'])
  })
})
