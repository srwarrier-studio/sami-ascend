import type { CatalogEntry } from './catalogClient'

const filler = new Set([
  'the', 'and', 'show', 'add', 'me', 'my', 'a', 'of', 'for', 'to', 'in', 'on', 'by', 'with', 'this', 'that', 'last', 'please',
  'who', 'are', 'you', 'what', 'how', 'why', 'when', 'where', 'which', 'can', 'does', 'did', 'tell', 'about', 'there', 'have', 'has',
  'was', 'were', 'our', 'their', 'your', 'its', 'any', 'all', 'give', 'want', 'need', 'see', 'get', 'hello', 'thanks', 'thank',
])

const stem = (word: string) => word.replace(/s$/, '')

const wordsOf = (text: string) =>
  text
    .toLowerCase()
    .split(/[^a-z]+/)
    .filter((word) => word.length > 2)

export const matchCatalog = (catalog: CatalogEntry[], sentence: string): CatalogEntry[] => {
  const words = wordsOf(sentence)
    .filter((word) => !filler.has(word))
    .map(stem)
  return catalog.filter((entry) => {
    const text = new Set(wordsOf(`${entry.title} ${entry.description}`).map(stem))
    return words.some((word) => text.has(word))
  })
}
