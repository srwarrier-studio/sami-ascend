import { Button, Card, ColorSwatch, Group, Stack, Text, Title } from '../src'

const shades = Array.from({ length: 10 }, (_, index) => index)
const status = [
  { name: 'Success', color: 'green' },
  { name: 'Info', color: 'blue' },
  { name: 'Warning', color: 'yellow' },
  { name: 'Danger', color: 'red' },
]
const sizes = ['xs', 'sm', 'md', 'lg', 'xl']

function Scale({ name, color }: { name: string; color: string }) {
  return (
    <Stack gap="xs">
      <Text size="xs" fw={600} c="dimmed" tt="uppercase">
        {name}
      </Text>
      <Group gap="xs">
        {shades.map((shade) => (
          <ColorSwatch key={shade} size={32} color={`var(--mantine-color-${color}-${shade})`} aria-label={`${name} ${shade}`} />
        ))}
      </Group>
    </Stack>
  )
}

export function TokensSection() {
  return (
    <Card>
      <Stack>
        <Title order={4}>Tokens</Title>
        <Scale name="Brand" color="brand" />
        <Scale name="Gray" color="gray" />
        <Group gap="lg">
          {status.map(({ name, color }) => (
            <Group key={name} gap="xs">
              <ColorSwatch size={20} color={`var(--mantine-color-${color}-6)`} aria-label={name} />
              <Text size="sm">{name}</Text>
            </Group>
          ))}
        </Group>
        <Stack gap="xs">
          <Title order={1}>Page title 28</Title>
          <Title order={2}>Section 24</Title>
          <Title order={4}>Panel 16</Title>
          <Text>Body text for tables and forms, 14 regular.</Text>
          <Text size="xs" c="dimmed">
            Caption 12
          </Text>
        </Stack>
        <Group align="flex-end">
          {sizes.map((size) => (
            <Button key={size} size={size}>
              {size}
            </Button>
          ))}
        </Group>
      </Stack>
    </Card>
  )
}
