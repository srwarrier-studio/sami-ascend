import { useEffect, useState } from 'react'
import { Badge, Chip, Drawer, Group, Progress, Stack, Text, TextInput, ThemeIcon, UnstyledButton } from '@mantine/core'
import {
  CalendarDotsIcon,
  CheckIcon,
  ChartBarIcon,
  ChartDonutIcon,
  ChartLineIcon,
  ChartLineUpIcon,
  GaugeIcon,
  GridFourIcon,
  HashIcon,
  ListNumbersIcon,
  MagnifyingGlassIcon,
  StackIcon,
  TableIcon,
} from '@phosphor-icons/react'
import type { Icon } from '@phosphor-icons/react'
import classes from './WidgetLibrary.module.css'

export type LibraryItem = { id: string; title: string; category: string; widget: string }

const kinds: Record<string, { label: string; icon: Icon }> = {
  KpiCard: { label: 'Key number', icon: HashIcon },
  LineChart: { label: 'Line chart', icon: ChartLineIcon },
  AreaChart: { label: 'Area chart', icon: ChartLineUpIcon },
  BarChart: { label: 'Bar chart', icon: ChartBarIcon },
  StackedBarChart: { label: 'Stacked bar chart', icon: StackIcon },
  DonutChart: { label: 'Donut chart', icon: ChartDonutIcon },
  GaugeChart: { label: 'Gauge', icon: GaugeIcon },
  RankedList: { label: 'Ranked list', icon: ListNumbersIcon },
  HeatmapChart: { label: 'Heatmap', icon: GridFourIcon },
  CalendarHeatmapChart: { label: 'Calendar heatmap', icon: CalendarDotsIcon },
  DataTable: { label: 'Table', icon: TableIcon },
}

type WidgetLibraryProps = { opened: boolean; onClose: () => void; items: LibraryItem[]; onPick: (id: string) => void; onRemove: (id: string) => void; counts?: Record<string, number>; limit?: { used: number; max: number } }

export function WidgetLibrary({ opened, onClose, items, onPick, onRemove, counts = {}, limit }: WidgetLibraryProps) {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('All')
  useEffect(() => {
    if (!opened) {
      setQuery('')
      setCategory('All')
    }
  }, [opened])
  const full = limit !== undefined && limit.used >= limit.max
  const text = query.trim().toLowerCase()
  const shown = items.filter((item) => `${item.title} ${kinds[item.widget]?.label ?? ''}`.toLowerCase().includes(text))
  const categories = [...new Set(items.map((item) => item.category))]
  const sections = categories
    .filter((name) => category === 'All' || category === name)
    .map((name) => ({ name, items: shown.filter((item) => item.category === name) }))
    .filter((section) => section.items.length > 0)

  return (
    <Drawer
      opened={opened}
      onClose={onClose}
      position="right"
      size="md"
      title="Widget library"
      withOverlay={false}
      closeOnClickOutside={false}
      lockScroll={false}
      trapFocus={false}
      classNames={{ content: classes.content, body: classes.body }}
    >
      <Stack gap="md" className={classes.head}>
        <TextInput
          aria-label="Search widgets"
          placeholder="Search widgets"
          leftSection={<MagnifyingGlassIcon size={16} />}
          value={query}
          onChange={(event) => setQuery(event.currentTarget.value)}
        />
        {limit && (
          <Stack gap={4}>
            <Progress value={(limit.used / limit.max) * 100} size="xs" radius="xl" aria-label="Widgets on this board" />
            <Text size="xs" c="dimmed">
              {full ? `Board is full: ${limit.max} of ${limit.max} widgets. Remove one to add another.` : `${limit.used} of ${limit.max} widgets on this board`}
            </Text>
          </Stack>
        )}
        <Chip.Group multiple={false} value={category} onChange={(value) => setCategory(value)}>
          <Group gap="xs">
            {['All', ...categories].map((name) => (
              <Chip key={name} value={name} size="xs">
                {name}
              </Chip>
            ))}
          </Group>
        </Chip.Group>
      </Stack>
      <Stack gap="md" className={classes.list}>
        {sections.length === 0 && <Text c="dimmed">No widgets match your search.</Text>}
        {sections.map((section) => (
          <Stack key={section.name} gap="xs">
            <Text size="xs" fw={600} c="dimmed" tt="uppercase">
              {section.name} · {section.items.length}
            </Text>
            {section.items.map((item) => {
              const kind = kinds[item.widget]
              const onBoard = counts[item.id] > 0
              return (
                <UnstyledButton key={item.id} className={classes.item} aria-label={`${onBoard ? 'Remove' : 'Add'} ${item.title}`} disabled={full && !onBoard} onClick={() => (onBoard ? onRemove(item.id) : onPick(item.id))}>
                  <div>
                    <Group gap="xs" wrap="nowrap">
                      <Text fw={600}>{item.title}</Text>
                      {onBoard && (
                        <Badge size="xs" variant="light" leftSection={<CheckIcon size={10} weight="bold" />}>
                          On board · click to remove
                        </Badge>
                      )}
                    </Group>
                    {kind && (
                      <Text size="xs" c="dimmed">
                        {kind.label}
                      </Text>
                    )}
                  </div>
                  {kind && (
                    <ThemeIcon className={classes.tile} variant="light" size={40} radius="md">
                      <kind.icon size={22} />
                    </ThemeIcon>
                  )}
                </UnstyledButton>
              )
            })}
          </Stack>
        ))}
      </Stack>
    </Drawer>
  )
}
