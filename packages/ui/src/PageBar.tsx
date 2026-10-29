import { ActionIcon, Button, Popover, SegmentedControl, Stack, Text, UnstyledButton } from '@mantine/core'
import { GearSixIcon, PlusIcon, SquaresFourIcon } from '@phosphor-icons/react'
import type { MotionMode } from './UiProvider'
import { presets } from './palettes'
import type { PresetName } from './palettes'
import classes from './PageBar.module.css'

export type PageBarTab = { id: string; name: string }
export type PageBarConfig = { palette: PresetName; scheme: 'light' | 'dark'; motion: MotionMode }

export type PageBarProps = {
  tabs: PageBarTab[]
  activeId: string
  config: PageBarConfig
  onSelect: (id: string) => void
  onAdd: () => void
  onArrange?: () => void
  onConfigChange: (config: PageBarConfig) => void
}

function QuickConfig({ config, onChange }: { config: PageBarConfig; onChange: PageBarProps['onConfigChange'] }) {
  const palettes = (Object.keys(presets) as PresetName[]).map((name) => ({ label: name[0].toUpperCase() + name.slice(1), value: name }))
  return (
    <Popover position="top-end" withArrow shadow="md" width={320}>
      <Popover.Target>
        <ActionIcon variant="subtle" color="gray" radius="xl" size={32} aria-label="Quick settings">
          <GearSixIcon size={18} />
        </ActionIcon>
      </Popover.Target>
      <Popover.Dropdown>
        <Stack gap="xs">
          <Text size="xs" fw={600} c="dimmed" tt="uppercase">
            Palette
          </Text>
          <SegmentedControl size="xs" radius="xl" aria-label="Palette" value={config.palette} data={palettes} onChange={(palette) => onChange({ ...config, palette: palette as PresetName })} />
          <Text size="xs" fw={600} c="dimmed" tt="uppercase">
            Theme
          </Text>
          <SegmentedControl
            size="xs"
            radius="xl"
            aria-label="Theme"
            value={config.scheme}
            data={[
              { label: 'Light', value: 'light' },
              { label: 'Dark', value: 'dark' },
            ]}
            onChange={(scheme) => onChange({ ...config, scheme: scheme as PageBarConfig['scheme'] })}
          />
          <Text size="xs" fw={600} c="dimmed" tt="uppercase">
            Motion
          </Text>
          <SegmentedControl
            size="xs"
            radius="xl"
            aria-label="Motion"
            value={config.motion}
            data={[
              { label: 'Full', value: 'full' },
              { label: 'Minimal', value: 'minimal' },
            ]}
            onChange={(motion) => onChange({ ...config, motion: motion as MotionMode })}
          />
        </Stack>
      </Popover.Dropdown>
    </Popover>
  )
}

export function PageBar({ tabs, activeId, config, onSelect, onAdd, onArrange, onConfigChange }: PageBarProps) {
  const editing = onArrange !== undefined
  return (
    <nav className={classes.bar} aria-label="Boards">
      <div className={classes.inner}>
        <div className={classes.tabs} role="tablist">
          {tabs.map((tab) => (
            <UnstyledButton
              key={tab.id}
              role="tab"
              aria-selected={tab.id === activeId}
              className={classes.tab}
              data-active={tab.id === activeId || undefined}
              disabled={editing && tab.id !== activeId}
              onClick={() => onSelect(tab.id)}
            >
              <span className={classes.name}>{tab.name}</span>
            </UnstyledButton>
          ))}
        </div>
        <Button
          size="xs"
          variant="subtle"
          miw="7.5rem"
          leftSection={onArrange ? <SquaresFourIcon size={14} /> : <PlusIcon size={14} />}
          onClick={onArrange ?? onAdd}
        >
          {onArrange ? 'Auto arrange' : 'Add'}
        </Button>
        <QuickConfig config={config} onChange={onConfigChange} />
      </div>
    </nav>
  )
}
