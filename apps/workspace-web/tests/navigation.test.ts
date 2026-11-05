import { activePath, navEntries, roleLabel } from '../src/navigation'

const labels = (roles: string[]) => navEntries(roles).map((entry) => entry.label)

describe('the navigation entries', () => {
  it('starts with Home and adds what the roles allow', () => {
    expect(labels(['purchase'])).toEqual(['Home', 'Purchase requisitions', 'New requisition'])
    expect(labels(['management'])).toEqual(['Home', 'Purchase requisitions'])
    expect(labels(['sales'])).toEqual(['Home', 'Sales orders', 'New sales order'])
  })

  it('gives an admin or a person without a menu role Home only', () => {
    expect(labels(['admin'])).toEqual(['Home'])
    expect(labels([])).toEqual(['Home'])
  })

  it('gives every entry an icon and a unique key', () => {
    const entries = navEntries(['purchase', 'sales'])
    entries.forEach((entry) => expect(entry.icon).toBeDefined())
    expect(new Set(entries.map((entry) => entry.key)).size).toBe(entries.length)
  })
})

describe('the active entry', () => {
  const entries = navEntries(['purchase'])

  it('is Home only on the home path', () => {
    expect(activePath(entries, '/')).toBe('/')
    expect(activePath(entries, '/purchase-requisitions')).toBe('/purchase-requisitions')
  })

  it('keeps the list active on a detail page', () => {
    expect(activePath(entries, '/purchase-requisitions/10000012')).toBe('/purchase-requisitions')
  })

  it('picks the new page and not the list on the new page', () => {
    expect(activePath(entries, '/purchase-requisitions/new')).toBe('/purchase-requisitions/new')
  })

  it('is none on a page the menu does not cover', () => {
    expect(activePath(entries, '/not-allowed')).toBeNull()
    expect(activePath(entries, '/sales-orders')).toBeNull()
  })

  it('does not treat a longer name as a child', () => {
    expect(activePath(entries, '/purchase-requisitions-old')).toBeNull()
  })
})

describe('the role label', () => {
  it('names the first role', () => {
    expect(roleLabel(['purchase', 'sales'])).toBe('Purchase')
    expect(roleLabel(['management'])).toBe('Management')
  })

  it('is empty without roles', () => {
    expect(roleLabel([])).toBe('')
  })
})
