import { useState } from 'react'
import { ActionIcon, Button, Popover, SegmentedControl, Stack, Text, TextInput, UnstyledButton } from '@mantine/core'
import { GearSixIcon, PencilSimpleIcon, PlusIcon } from '@phosphor-icons/react'
import type { MotionMode } from './UiProvider'
import { presets } from './palettes'
import type { PresetName } from './palettes'
import classes from './PageBar.module.css'

export type PageBarTab = { id: string; name: string }
export type PageBarConfig = { palette: PresetName; scheme: 'light' | 'dark'; motion: MotionMode }

export type PageBarProps = {
  tabs: PageBarTab[]
  activeId: string
  editing?: boolean
  config: PageBarConfig
  onSelect: (id: string) => void
  onAdd: () => void
  onRename: (id: string, name: string) => void
  onConfigChange: (config: PageBarConfig) => void
}

function RenameField({ tab, onRename, onDone }: { tab: PageBarTab; onRename: PageBarProps['onRename']; onDone: () => void }) {
  const [value, setValue] = useState(tab.name)
  const save = () => {
    const name = value.trim()
    if (name) onRename(tab.id, name)
    onDone()
  }
  return (
    <TextInput
      className={classes.rename}
      size="xs"
      aria-label={`Rename ${tab.name}`}
      value={value}
      autoFocus
      onChange={(event) => setValue(event.currentTarget.value)}
      onBlur={save}
      onKeyDown={(event) => {
        if (event.key === 'Enter') save()
        if (event.key === 'Escape') onDone()
      }}
    />
  )
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

export function PageBar({ tabs, activeId, editing = false, config, onSelect, onAdd, onRename, onConfigChange }: PageBarProps) {
  const [renaming, setRenaming] = useState<string | null>(null)
  return (
    <nav className={classes.bar} aria-label="Boards">
      <div className={classes.inner}>
        <div className={classes.tabs} role="tablist">
          {tabs.map((tab) => (
            <div key={tab.id} className={classes.tab} data-active={tab.id === activeId || undefined}>
              {editing && renaming === tab.id ? (
                <RenameField tab={tab} onRename={onRename} onDone={() => setRenaming(null)} />
              ) : (
                <>
                  <UnstyledButton
                    role="tab"
                    aria-selected={tab.id === activeId}
                    className={classes.name}
                    onClick={() => onSelect(tab.id)}
                    onDoubleClick={() => editing && setRenaming(tab.id)}
                  >
                    {tab.name}
                  </UnstyledButton>
                  {editing && (
                    <ActionIcon size={20} variant="subtle" color="gray" radius="xl" aria-label={`Rename ${tab.name}`} onClick={() => setRenaming(tab.id)}>
                      <PencilSimpleIcon size={12} />
                    </ActionIcon>
                  )}
                </>
              )}
            </div>
          ))}
        </div>
        <Button size="xs" variant="subtle" leftSection={<PlusIcon size={14} />} onClick={onAdd}>
          Add
        </Button>
        <QuickConfig config={config} onChange={onConfigChange} />
      </div>
    </nav>
  )
}
