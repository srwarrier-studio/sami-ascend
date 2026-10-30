import type { CatalogEntry } from './catalogClient'

const filler = new Set(['the', 'and', 'show', 'add', 'me', 'my', 'a', 'of', 'for', 'to', 'in', 'on', 'by', 'with', 'this', 'that', 'last', 'please'])

export const matchCatalog = (catalog: CatalogEntry[], sentence: string): CatalogEntry[] => {
  const words = sentence
    .toLowerCase()
    .split(/[^a-z]+/)
    .filter((word) => word.length > 2 && !filler.has(word))
  return catalog.filter((entry) => {
    const text = `${entry.title} ${entry.description}`.toLowerCase()
    return words.some((word) => text.includes(word))
  })
}
