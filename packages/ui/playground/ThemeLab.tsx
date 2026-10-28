import { Group, SegmentedControl, Stack, Text, presets } from '../src'
import type { MotionMode, PresetName, RadiusMode } from '../src'

export type Lab = {
  palette: PresetName
  radius: RadiusMode
  motion: MotionMode
  layout: 'top' | 'side'
}

export const defaultLab: Lab = { palette: 'teal', radius: 'soft', motion: 'full', layout: 'top' }

type Choice<T extends string> = { label: string; value: T }

const paletteChoices = (Object.keys(presets) as PresetName[]).map((name) => ({
  label: name[0].toUpperCase() + name.slice(1),
  value: name,
}))

function Switch<T extends string>({
  label,
  value,
  choices,
  onChange,
}: {
  label: string
  value: T
  choices: Choice<T>[]
  onChange: (value: T) => void
}) {
  return (
    <Stack gap="xs">
      <Text size="xs" fw={600} c="dimmed" tt="uppercase">
        {label}
      </Text>
      <SegmentedControl aria-label={label} size="xs" radius="xl" value={value} data={choices} onChange={(next) => onChange(next as T)} />
    </Stack>
  )
}

export function ThemeLab({ lab, onChange }: { lab: Lab; onChange: (lab: Lab) => void }) {
  return (
    <Group align="flex-end" gap="lg" role="group" aria-label="Theme lab">
      <Switch label="Palette" value={lab.palette} choices={paletteChoices} onChange={(palette) => onChange({ ...lab, palette })} />
      <Switch
        label="Radius"
        value={lab.radius}
        choices={[
          { label: 'Soft', value: 'soft' },
          { label: 'Sharp', value: 'sharp' },
        ]}
        onChange={(radius) => onChange({ ...lab, radius })}
      />
      <Switch
        label="Motion"
        value={lab.motion}
        choices={[
          { label: 'Full', value: 'full' },
          { label: 'Minimal', value: 'minimal' },
        ]}
        onChange={(motion) => onChange({ ...lab, motion })}
      />
      <Switch
        label="Layout"
        value={lab.layout}
        choices={[
          { label: 'Top', value: 'top' },
          { label: 'Side', value: 'side' },
        ]}
        onChange={(layout) => onChange({ ...lab, layout })}
      />
    </Group>
  )
}
