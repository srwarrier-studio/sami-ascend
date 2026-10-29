export type HelpText = { shows: string; read: string }

export const DEFAULT_MEASURE = 'the value'

const upper = (text: string) => text.charAt(0).toUpperCase() + text.slice(1)

export const help = {
  KpiCard: (m: string) => ({
    shows: `The headline figure for ${m}.`,
    read: `The arrow and percent show how ${m} changed against the previous period: green means up and red means down. The small line is the recent trend.`,
  }),
  LineChart: (m: string) => ({
    shows: `How ${m} changes from one label to the next, such as day to day or month to month.`,
    read: `Each point is the figure for ${m} at one label, and the dot marks the latest. A grey line, when shown, is the previous period for comparison. Hover for the exact figure.`,
  }),
  AreaChart: (m: string) => ({
    shows: `How ${m} builds up or changes over time.`,
    read: `The height at any point is ${m} at that label, so a larger filled area means more overall. Hover for the exact figure.`,
  }),
  BarChart: (m: string) => ({
    shows: `${upper(m)} for each label, such as each month.`,
    read: `A taller bar means higher ${m}. The darker bar is the latest. Hover a bar for the exact figure.`,
  }),
  StackedBarChart: (m: string) => ({
    shows: `${upper(m)} for each label, split into parts.`,
    read: `Stacked bars add the parts up: the full height is the total ${m} and each colour is one part. Grouped bars put the parts side by side so you can compare them. The legend names the colours.`,
  }),
  DonutChart: (m: string) => ({
    shows: `How ${m} is shared between categories.`,
    read: `Each slice is one category's share of the total ${m}, and a bigger slice is a bigger share. The centre shows the largest share and the list below gives every share.`,
  }),
  GaugeChart: (m: string) => ({
    shows: `How far ${m} has come against its target.`,
    read: `The ring fills as ${m} approaches the target and the centre shows the percent reached. A number above 100% means the target was beaten.`,
  }),
  HeatmapChart: (m: string) => ({
    shows: `${upper(m)} for every pair of two categories, such as weekday and hour.`,
    read: `Each square is one pair. Colour strength follows ${m}: stronger means more and fainter means less. The bar below gives the lowest and the highest figure. Hover a square for the exact figure.`,
  }),
  CalendarHeatmapChart: (m: string) => ({
    shows: `${upper(m)} on each day of the period.`,
    read: `Each square is one day. Colour strength follows ${m}: a stronger square is a day with more and a faint square is a day with less or no data. Columns are weeks starting on Monday and months are named along the top. Hover a day for the exact figure.`,
  }),
  RankedList: (m: string) => ({
    shows: `Items ranked by ${m}, highest first.`,
    read: `The first item is the highest for ${m}. The bar under each name shows its size compared with the first item.`,
  }),
  DataTable: () => ({
    shows: 'Rows of detail, such as recent invoices.',
    read: 'Each row is one record. Numbers are aligned to the right and a coloured tag shows the status.',
  }),
} satisfies Record<string, (measure: string) => HelpText>

export type WidgetName = keyof typeof help

export const helpText = (name: WidgetName, measure?: string): HelpText => help[name](measure ?? DEFAULT_MEASURE)
