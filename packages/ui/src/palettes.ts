import type { MantineColorsTuple } from '@mantine/core'

export type Palette = {
  primaryColor: string
  primaryShade: number
  colors: Record<string, MantineColorsTuple>
}

export type PresetName = 'midnight' | 'teal' | 'blue' | 'indigo' | 'graphite' | 'copper'

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

const midnightBrand: MantineColorsTuple = [
  '#eef3ff',
  '#dbe6fe',
  '#b8ccfb',
  '#8fb0f6',
  '#6a93ee',
  '#4f7fe8',
  '#3b6fe0',
  '#2f5bc2',
  '#254a9f',
  '#1b3a80',
]

const midnightGray: MantineColorsTuple = [
  '#f5f7fb',
  '#eef1f7',
  '#e4e9f1',
  '#d6dde8',
  '#b4bfd0',
  '#8793ab',
  '#5a6680',
  '#3f4a63',
  '#2a3350',
  '#1b2340',
]

const midnightDark: MantineColorsTuple = [
  '#e6ecf8',
  '#c3cfe8',
  '#97a8cc',
  '#7284ad',
  '#2a3a63',
  '#1e2c50',
  '#16223f',
  '#0d1630',
  '#091024',
  '#050a1a',
]

function withBrand(brand: MantineColorsTuple): Palette {
  return { primaryColor: 'brand', primaryShade: 6, colors: { brand, gray: slate, dark: slateDark } }
}

export const presets: Record<PresetName, Palette> = {
  midnight: { primaryColor: 'brand', primaryShade: 6, colors: { brand: midnightBrand, gray: midnightGray, dark: midnightDark } },
  teal: withBrand(teal),
  blue: withBrand(blue),
  indigo: withBrand(indigo),
  graphite: withBrand(graphite),
  copper: withBrand(copper),
}

export type Surfaces = { canvas: string; surface: string; border: string; shadow: string }

export const premiumSurfaces: { light: Surfaces; dark: Surfaces } = {
  light: {
    canvas: '#f3f5fa',
    surface: '#ffffff',
    border: 'rgb(20 35 80 / 9%)',
    shadow: '0 1px 2px rgb(16 24 64 / 5%), 0 8px 24px rgb(16 24 64 / 6%)',
  },
  dark: {
    canvas: '#0b1329',
    surface: '#111b36',
    border: 'rgb(143 180 255 / 14%)',
    shadow: '0 0 0 1px rgb(143 180 255 / 4%), 0 10px 30px rgb(0 0 0 / 35%)',
  },
}

export const workspacePalette: Palette = presets.blue

export const synapsePalette: Palette = presets.midnight
