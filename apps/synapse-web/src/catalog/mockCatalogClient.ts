import { fixtureEntries, fixtures } from './fixtures'
import type { CatalogClient } from './catalogClient'

export class MockCatalogClient implements CatalogClient {
  async list(_company: string | null) {
    return fixtureEntries
  }

  async summary(_company: string | null, currency: string) {
    return { asOf: '2026-11-02T17:11:00+00:00', currency, sentences: ['Sales this month are \u20b93,40,000 (1\u201320 Nov), up 6.3% on 1\u201320 Oct.', 'Acme Ltd moved most: \u20b950,000 more than on 1\u201320 Oct.'] }
  }

  async data(id: string, _company: string | null, _currency: string, _top?: number) {
    const fixture = fixtures.find((candidate) => candidate.entry.id === id)
    if (!fixture) throw new Error('CATALOG_ENTRY_NOT_FOUND')
    return fixture.props
  }
}
