import { Badge, Button, Group, Stack, Text } from '@sami/ui'
import classes from '../boards/Board.module.css'
import type { IntentReading, IntentReason } from './intentClient'

const percent = (probability: number) => `${Math.round(probability * 100)}%`
const readable = (id: string) => `${id.charAt(0).toUpperCase()}${id.slice(1).replace(/_/g, ' ')}`

const REFUSALS: Record<IntentReason, (domain: string | null) => string> = {
  not_about_business: () => 'This does not look like a question about our figures.',
  not_sure: () => 'I am not sure what you mean.',
  no_scenarios: (domain) => `This is about ${domain ?? 'a topic'}, which I cannot answer yet.`,
  nothing_matched: (domain) => `I could not tell which figure you want from ${domain ?? 'this topic'}.`,
}

type IntentCardProps = { reading: IntentReading; answered?: boolean; onAsk?: (question: string) => void }

export function IntentCard({ reading, answered = false, onAsk }: IntentCardProps) {
  const refused = reading.reason !== null && !answered
  return (
    <details open={refused} className={classes.reading}>
      <summary>How was this read?</summary>
      <Stack gap={2} mt="xs" aria-label="How the question was read">
        <Group gap="xs">
          <Badge variant="light" size="xs" tt="none">
            Reading
          </Badge>
          {reading.domain !== null && !refused && (
            <Text size="xs" fw={600}>
              Understood as {reading.domain} ({percent(reading.domainProbability)})
            </Text>
          )}
        </Group>
        {refused && reading.reason !== null && (
          <Text size="xs" c="dimmed">
            {REFUSALS[reading.reason](reading.domain)}
            {reading.didYouMean.length > 0 && ' Did you mean'}
          </Text>
        )}
        {refused && reading.didYouMean.length > 0 && (
          <Group gap="xs">
            {reading.didYouMean.map((domain) => (
              <Button key={domain} size="compact-xs" variant="light" onClick={() => onAsk?.(`Show ${domain}`)}>
                {domain}
              </Button>
            ))}
          </Group>
        )}
        {reading.scenarios.map((scenario) => (
          <Text key={scenario.id} size="xs" c="dimmed">
            {readable(scenario.id)}, {percent(scenario.probability)}
          </Text>
        ))}
      </Stack>
    </details>
  )
}
