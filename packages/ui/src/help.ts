export type Help = { shows: string; read: string }

export const help = {
  KpiCard: {
    shows: 'One headline number for the period.',
    read: 'The arrow and percent show the change against the previous period. Green means it rose and red means it fell. The small line on the right is the recent trend.',
  },
  LineChart: {
    shows: 'How a value changes across ordered labels such as days or months.',
    read: 'Each point is one label. The dot marks the latest value. When a grey line is shown it is the previous period, so you can compare the two. Hover for the exact value.',
  },
  AreaChart: {
    shows: 'How a value builds up or changes over time.',
    read: 'The height at any point is the value, so a larger filled area means more in total. Hover for the exact value.',
  },
  BarChart: {
    shows: 'A value for each label, such as sales per month.',
    read: 'Taller bars mean higher values. The darker bar is the latest. Hover a bar for its exact value.',
  },
  StackedBarChart: {
    shows: 'A value for each label, split into parts.',
    read: 'Stacked bars add the parts up, so the full height is the total and each colour is one part. Grouped bars put the parts side by side so you can compare them. The legend names the colours.',
  },
  DonutChart: {
    shows: 'How a total is shared between categories.',
    read: 'Each slice is one category and a bigger slice is a bigger share. The centre shows the largest share. The list below gives every share.',
  },
  GaugeChart: {
    shows: 'Progress of a value against its target.',
    read: 'The ring fills as the value approaches the target. The centre shows the percent reached, and a number above 100% means the target was beaten.',
  },
  HeatmapChart: {
    shows: 'A value for every pair of two categories, such as weekday and hour.',
    read: 'Darker squares are higher values and lighter squares are lower. The bar below gives the lowest and the highest value. Hover a square for its exact value.',
  },
  CalendarHeatmapChart: {
    shows: 'A value for every day of a period, such as sales per day.',
    read: 'Each square is one day. Columns are weeks starting on Monday, rows are weekdays and month names run along the top. Darker means a higher value and a faint square means no data. Hover a day for the exact value.',
  },
  RankedList: {
    shows: 'Items ranked from the highest value to the lowest.',
    read: 'The first item is the highest. The bar under each name shows its size compared with the first item.',
  },
  DataTable: {
    shows: 'Rows of detail, such as recent invoices.',
    read: 'Each row is one record. Numbers are aligned to the right and a coloured tag shows the status.',
  },
} satisfies Record<string, Help>

export type WidgetName = keyof typeof help
