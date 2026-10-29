import { mockLibrary } from '@sami/ui'
import type { CatalogEntry } from './catalog'

export const libraryEntries: CatalogEntry[] = mockLibrary.map(({ props, ...item }) => ({ ...item, load: async () => props }))
