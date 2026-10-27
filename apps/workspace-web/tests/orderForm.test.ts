import {
  addItem,
  initialForm,
  mapDetails,
  removeItem,
  toNewOrder,
} from '../src/orderForm'

describe('initial form', () => {
  it('has type OR, currency INR and one empty item', () => {
    const form = initialForm()
    expect(form).toMatchObject({ salesOrderType: 'OR', transactionCurrency: 'INR', soldToParty: '' })
    expect(form.items).toEqual([{ material: '', quantity: '', quantityUnit: '' }])
  })
})

describe('items', () => {
  it('adds a row', () => {
    expect(addItem(initialForm()).items).toHaveLength(2)
  })

  it('removes the chosen row', () => {
    let form = addItem(initialForm())
    form = { ...form, items: [{ ...form.items[0], material: 'A' }, { ...form.items[1], material: 'B' }] }
    expect(removeItem(form, 0).items.map((i) => i.material)).toEqual(['B'])
  })

  it('keeps the last row', () => {
    expect(removeItem(initialForm(), 0).items).toHaveLength(1)
  })
})

describe('toNewOrder', () => {
  it('trims values and sends an empty date as null', () => {
    const form = {
      ...initialForm(),
      soldToParty: ' 0000100001 ',
      items: [{ material: ' RM-1001 ', quantity: ' 5.5 ', quantityUnit: ' KG ' }],
    }
    expect(toNewOrder(form)).toEqual({
      sales_order_type: 'OR',
      sold_to_party: '0000100001',
      transaction_currency: 'INR',
      requested_delivery_date: null,
      items: [{ material: 'RM-1001', quantity: '5.5', quantity_unit: 'KG' }],
    })
  })

  it('keeps a typed date', () => {
    const form = { ...initialForm(), requestedDeliveryDate: '2026-11-05' }
    expect(toNewOrder(form).requested_delivery_date).toBe('2026-11-05')
  })
})

describe('mapDetails', () => {
  const detail = (target: string, message = 'bad') => ({ code: 'X', target, message })

  it('maps header targets', () => {
    expect(mapDetails([detail('SoldToParty', 'Unknown customer')], 1).fields).toEqual({
      soldToParty: 'Unknown customer',
    })
  })

  it('maps item targets by row', () => {
    const result = mapDetails([detail('_Item/1/Quantity', 'Must be positive')], 2)
    expect(result.fields).toEqual({ 'items.1.quantity': 'Must be positive' })
    expect(result.general).toEqual([])
  })

  it('sends unmatched targets to general', () => {
    const result = mapDetails([detail('', 'Add an item'), detail('_Item/5/Quantity', 'gone'), detail('Other')], 1)
    expect(result.fields).toEqual({})
    expect(result.general).toEqual(['Add an item', 'gone', 'bad'])
  })

  it('keeps the first message when a field has two', () => {
    const result = mapDetails([detail('SoldToParty', 'first'), detail('SoldToParty', 'second')], 1)
    expect(result.fields.soldToParty).toBe('first')
    expect(result.general).toEqual(['second'])
  })
})
