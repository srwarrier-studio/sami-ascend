import type { MantineColorsTuple } from '@mantine/core'

export type Palette = {
  primaryColor: string
  primaryShade: number
  colors: Record<string, MantineColorsTuple>
}

export type PresetName = 'teal' | 'blue' | 'indigo' | 'graphite' | 'copper'

const slate: MantineColorsTuple = [
  '#f6f8fa',
  '#edf1f4',
  '#e5eaee',
  '#d9e0e6',
  '#b6c0ca',
  '#8795a3',
  '#536070',
  '#3a4654',
  '#26303b',
  '#1c2530',
]

const slateDark: MantineColorsTuple = [
  '#e7edf0',
  '#c9d4db',
  '#99a7b1',
  '#7a8a96',
  '#26343b',
  '#1f2a30',
  '#151e23',
  '#0d1418',
  '#091014',
  '#050a0d',
]

const teal: MantineColorsTuple = [
  '#eef8f7',
  '#dcf0ee',
  '#b9e0dc',
  '#8fcbc5',
  '#5fb0a9',
  '#2f938c',
  '#0b7a75',
  '#08615d',
  '#064b48',
  '#043634',
]

const blue: MantineColorsTuple = [
  '#eff4fc',
  '#e0eaf9',
  '#c1d5f3',
  '#9bbaea',
  '#6f98de',
  '#4579cf',
  '#1f5fbf',
  '#194c99',
  '#133a76',
  '#0d2955',
]

const indigo: MantineColorsTuple = [
  '#f1f0fb',
  '#e8e6f8',
  '#d0ccf0',
  '#b0aae4',
  '#8e86d6',
  '#6e65c7',
  '#4f46b8',
  '#3c3591',
  '#2d2870',
  '#1f1b4f',
]

const graphite: MantineColorsTuple = [
  '#f3f5f7',
  '#e3e8ed',
  '#c7d0d9',
  '#a3b0bd',
  '#7b8b9b',
  '#566677',
  '#2b3a4a',
  '#1c2530',
  '#141b23',
  '#0d1218',
]

const copper: MantineColorsTuple = [
  '#fcf4ec',
  '#faebdd',
  '#f3d3b6',
  '#eab88a',
  '#de985a',
  '#cc7a31',
  '#b25a12',
  '#8a430a',
  '#683308',
  '#472305',
]

function withBrand(brand: MantineColorsTuple): Palette {
  return { primaryColor: 'brand', primaryShade: 6, colors: { brand, gray: slate, dark: slateDark } }
}

export const presets: Record<PresetName, Palette> = {
  teal: withBrand(teal),
  blue: withBrand(blue),
  indigo: withBrand(indigo),
  graphite: withBrand(graphite),
  copper: withBrand(copper),
}

export const workspacePalette: Palette = presets.blue

export const synapsePalette: Palette = presets.teal
