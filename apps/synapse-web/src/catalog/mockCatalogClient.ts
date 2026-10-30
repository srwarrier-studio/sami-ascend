import { fixtureEntries, fixtures } from './fixtures'
import type { CatalogClient } from './catalogClient'

export class MockCatalogClient implements CatalogClient {
  async list() {
    return fixtureEntries
  }

  async data(id: string) {
    const fixture = fixtures.find((candidate) => candidate.entry.id === id)
    if (!fixture) throw new Error('CATALOG_ENTRY_NOT_FOUND')
    return fixture.props
  }
}
