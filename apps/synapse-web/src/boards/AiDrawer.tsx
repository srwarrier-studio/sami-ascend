import { useState } from 'react'
import type { SyntheticEvent } from 'react'
import { Alert, Button, Drawer, Stack, Text, TextInput } from '@sami/ui'
import { matchCatalog } from '../catalog/catalog'

type AiDrawerProps = { opened: boolean; onClose: () => void; onAdd: (catalogIds: string[]) => void }

export function AiDrawer({ opened, onClose, onAdd }: AiDrawerProps) {
  const [sentence, setSentence] = useState('')
  const [result, setResult] = useState<string | null>(null)

  const submit = (event: SyntheticEvent) => {
    event.preventDefault()
    const matches = matchCatalog(sentence)
    if (matches.length === 0) {
      setResult('No widget matches that. Try words like sales, customers or orders.')
      return
    }
    onAdd(matches.map((entry) => entry.id))
    setResult(`Added: ${matches.map((entry) => entry.title).join(', ')}`)
    setSentence('')
  }

  return (
    <Drawer opened={opened} onClose={onClose} position="right" title="AI Mode">
      <form onSubmit={submit}>
        <Stack>
          <Text size="sm" c="dimmed">
            Describe what you want to see. Only predefined widgets are added.
          </Text>
          <TextInput label="What do you want on this board?" value={sentence} onChange={(event) => setSentence(event.currentTarget.value)} />
          <Button type="submit">Add widgets</Button>
          {result && <Alert color="blue">{result}</Alert>}
        </Stack>
      </form>
    </Drawer>
  )
}
