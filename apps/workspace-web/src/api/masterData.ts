import { WORKSPACE_URL } from '../config'

export type Plant = { plant: string; name: string; company_code: string }

export type Material = {
  material: string
  description: string
  unit: string
  iso_unit: string
  material_group: string
  material_type: string
  plants: string[]
}

export type Partner = { number: string; name: string; company_codes: string[] }

export type MasterDataClient = {
  plants: () => Promise<Plant[]>
  materials: (query: string, plant?: string) => Promise<Material[]>
  customers: (query: string) => Promise<Partner[]>
  suppliers: (query: string) => Promise<Partner[]>
}

const base = `${WORKSPACE_URL}/v1/workspace/master-data`
const PAGE = 20

async function read(path: string, params: Record<string, string>) {
  const search = new URLSearchParams(Object.entries(params).filter(([, value]) => value !== ''))
  const query = search.toString()
  const response = await fetch(`${base}/${path}${query ? `?${query}` : ''}`, { credentials: 'include' })
  if (!response.ok) throw new Error(`${path} failed: ${response.status}`)
  return response.json()
}

export const masterDataClient: MasterDataClient = {
  async plants() {
    return (await read('plants', {})).plants
  },
  async materials(query, plant) {
    return (await read('materials', { q: query, plant: plant ?? '', top: String(PAGE) })).materials
  },
  async customers(query) {
    return (await read('customers', { q: query, top: String(PAGE) })).customers
  },
  async suppliers(query) {
    return (await read('suppliers', { q: query, top: String(PAGE) })).suppliers
  },
}
