export type Company = { id: string; name: string; logoLetter: string; color: string }

export const ALL_COMPANIES = 'all'

export const companies: Company[] = [
  { id: 'sabinsa', name: 'Sami Sabinsa Group Limited', logoLetter: 'S', color: '#0f766e' },
  { id: 'neutraceuticals', name: 'Sami Neutraceuticals Private Limited', logoLetter: 'S', color: '#1d4ed8' },
  { id: 'organica', name: 'Organica Aromatic', logoLetter: 'O', color: '#b45309' },
  { id: ALL_COMPANIES, name: 'All companies', logoLetter: 'G', color: '#475569' },
]

export const findCompany = (id: string) => companies.find((company) => company.id === id)

export const knownCompanyIds = (ids: string[]) => ids.filter((id) => findCompany(id))
