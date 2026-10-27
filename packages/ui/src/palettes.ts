import type { MantineColorsTuple } from '@mantine/core'

export type Palette = {
  primaryColor: string
  primaryShade: number
  colors: Record<string, MantineColorsTuple>
}

const slate: MantineColorsTuple = [
  '#f7f8fa',
  '#f1f3f6',
  '#e6e9ee',
  '#d8dce3',
  '#b8bec9',
  '#8e97a6',
  '#677082',
  '#4a5262',
  '#2a303b',
  '#14171c',
]

const blue: MantineColorsTuple = [
  '#eaf2ff',
  '#d3e4ff',
  '#a6c8ff',
  '#76a9ff',
  '#4f90ff',
  '#337dff',
  '#0b63f6',
  '#0052d9',
  '#0045b8',
  '#003894',
]

const teal: MantineColorsTuple = [
  '#e6faf7',
  '#c8f3ec',
  '#96e7d9',
  '#5fdac4',
  '#33cdb3',
  '#16c3a8',
  '#0aa88f',
  '#058c78',
  '#04705f',
  '#035447',
]

export const workspacePalette: Palette = {
  primaryColor: 'brand',
  primaryShade: 6,
  colors: { brand: blue, gray: slate },
}

export const synapsePalette: Palette = {
  primaryColor: 'brand',
  primaryShade: 7,
  colors: { brand: teal, gray: slate },
}
