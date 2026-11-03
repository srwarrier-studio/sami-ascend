import { useEffect, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Button, Card, Group, SparkleIcon, Stack, Text } from '@sami/ui'
import { REFRESH_MS, CURRENCY } from '../catalog/CatalogWidget'
import type { CatalogClient, Summary } from '../catalog/catalogClient'
import classes from './Board.module.css'

type SummaryStripProps = { client: CatalogClient; company: string | null; widgets: string[]; refreshMs?: number }

export function SummaryStrip({ client, company, widgets, refreshMs = REFRESH_MS }: SummaryStripProps) {
  const navigate = useNavigate()
  const [summary, setSummary] = useState<Summary | null>(null)
  const ids = [...new Set(widgets)].sort().join(',')

  useEffect(() => {
    let current = true
    const load = () =>
      client
        .summary(company, CURRENCY, ids === '' ? [] : ids.split(','))
        .then((next) => current && setSummary(next))
        .catch(() => current && setSummary(null))
    load()
    const timer = setInterval(load, refreshMs)
    return () => {
      current = false
      clearInterval(timer)
    }
  }, [client, company, ids, refreshMs])

  if (!summary || summary.sentences.length === 0) return null
  return (
    <Card className={classes.summary} aria-label="Summary">
      <Group justify="space-between" align="flex-start" wrap="nowrap">
        <Stack gap={4}>
          {summary.sentences.map((sentence) => (
            <Text key={sentence}>{sentence}</Text>
          ))}
        </Stack>
        <Button variant="subtle" size="compact-sm" leftSection={<SparkleIcon size={14} weight="fill" />} onClick={() => navigate({ to: '/ai' })}>
          Ask AI for more
        </Button>
      </Group>
    </Card>
  )
}
