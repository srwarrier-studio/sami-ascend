import { addItem, emptyItem, fieldKey, initialForm, mapDetails, removeItem, toNewRequisition } from '../src/requisitionForm'

describe('the form', () => {
  it('starts with one empty row and adds and removes rows', () => {
    let form = initialForm()
    expect(form.items).toEqual([emptyItem()])
    form = addItem(form)
    expect(form.items).toHaveLength(2)
    expect(removeItem(form, 0).items).toHaveLength(1)
    expect(removeItem(removeItem(form, 0), 0).items).toHaveLength(1)
  })

  it('builds the body trimmed, with the text only when given', () => {
    const form = {
      description: ' Spares ',
      items: [
        { material: ' RM-1001 ', plant: '1000', quantity: ' 5 ', unit: 'KG', deliveryDate: '2026-12-01', text: '' },
        { material: 'RM-1002', plant: '1000', quantity: '2', unit: 'KG', deliveryDate: '2026-12-02', text: ' urgent ' },
      ],
    }
    expect(toNewRequisition(form)).toEqual({
      description: 'Spares',
      items: [
        { material: 'RM-1001', plant: '1000', quantity: '5', unit: 'KG', delivery_date: '2026-12-01' },
        { material: 'RM-1002', plant: '1000', quantity: '2', unit: 'KG', delivery_date: '2026-12-02', text: 'urgent' },
      ],
    })
  })
})

describe('mapping SAP details to fields', () => {
  it('puts each message on its row and field', () => {
    const errors = mapDetails(
      [
        { code: 'MATERIAL_UNKNOWN', target: 'items/1/material', message: 'No such material' },
        { code: 'DELIVERY_DATE_IN_PAST', target: 'items/0/delivery_date', message: 'In the past' },
        { code: 'X', target: 'description', message: 'Bad description' },
      ],
      2,
    )
    expect(errors.fields).toEqual({
      [fieldKey(1, 'material')]: 'No such material',
      [fieldKey(0, 'deliveryDate')]: 'In the past',
      description: 'Bad description',
    })
    expect(errors.general).toEqual([])
  })

  it('keeps the first message for a field and shows the rest as general', () => {
    const errors = mapDetails(
      [
        { code: 'A', target: 'items/0/quantity', message: 'first' },
        { code: 'B', target: 'items/0/quantity', message: 'second' },
      ],
      1,
    )
    expect(errors.fields[fieldKey(0, 'quantity')]).toBe('first')
    expect(errors.general).toEqual(['second'])
  })

  it.each([['items/5/material'], ['items'], ['items/0/surprise'], ['release_code']])('shows %s as a general message', (target) => {
    expect(mapDetails([{ code: 'A', target, message: 'm' }], 1)).toEqual({ fields: {}, general: ['m'] })
  })
})
