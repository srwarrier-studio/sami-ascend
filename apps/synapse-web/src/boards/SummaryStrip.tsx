import { useEffect, useState } from 'react'
import { Card, Stack, Text, clockTime } from '@sami/ui'
import { REFRESH_MS, CURRENCY } from '../catalog/CatalogWidget'
import type { CatalogClient, Summary } from '../catalog/catalogClient'
import classes from './Board.module.css'

type SummaryStripProps = { client: CatalogClient; company: string | null; refreshMs?: number }

export function SummaryStrip({ client, company, refreshMs = REFRESH_MS }: SummaryStripProps) {
  const [summary, setSummary] = useState<Summary | null>(null)

  useEffect(() => {
    let current = true
    const load = () =>
      client
        .summary(company, CURRENCY)
        .then((next) => current && setSummary(next))
        .catch(() => current && setSummary(null))
    load()
    const timer = setInterval(load, refreshMs)
    return () => {
      current = false
      clearInterval(timer)
    }
  }, [client, company, refreshMs])

  if (!summary || summary.sentences.length === 0) return null
  const time = clockTime(summary.asOf)
  return (
    <Card className={classes.summary} aria-label="Summary">
      <Stack gap={4}>
        {summary.sentences.map((sentence) => (
          <Text key={sentence}>{sentence}</Text>
        ))}
        {time && (
          <Text size="xs" c="dimmed">
            {`as of ${time}`}
          </Text>
        )}
      </Stack>
    </Card>
  )
}
