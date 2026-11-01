import { useEffect, useRef, useState } from 'react'
import type { SyntheticEvent } from 'react'
import { useNavigate, useRouteContext } from '@tanstack/react-router'
import { ActionIcon, ArrowLeftIcon, Badge, Button, Group, Modal, PageHeader, PaperPlaneRightIcon, SparkleIcon, Stack, Text, TextInput, Title, WidgetCell, WidgetGrid } from '@sami/ui'
import { AnswerBlocks } from '../ai/AnswerBlocks'
import { SHOWN_PROBLEMS } from '../ai/agentsClient'
import type { AgentAnswer, AgentContext, AnswerBlock } from '../ai/agentsClient'
import { IntentCard } from '../ai/IntentCard'
import { IntentDataUnavailable } from '../ai/intentClient'
import type { IntentReading, IntentReply } from '../ai/intentClient'
import { BUILDER } from '../ai/chatPlanner'
import type { ChatBoard } from '../ai/chatPlanner'
import { BoardGrid } from '../boards/BoardGrid'
import { SaveBoardModal } from '../boards/SaveBoardModal'
import { buildWidgets } from '../boards/layout'
import { CatalogWidget } from '../catalog/CatalogWidget'
import classes from '../boards/Board.module.css'

type Message = { from: 'you' | 'ai'; text: string; catalogIds?: string[]; board?: ChatBoard; agent?: AgentAnswer; blocks?: AnswerBlock[]; intent?: IntentReading | null }

const UNAVAILABLE = 'The analysis service is not available right now.'
const NO_FIGURES = 'The figures are not available right now.'
const unusablePeriod = (periods: string[]) => `I could not use the period in your question (I read ${periods.join(' and ')}). Ask for one period that has already started.`

const examples = ['Show top customers and top materials', `${BUILDER} build me a sales board`, `${BUILDER} build an inventory board`]

export function AiPage() {
  const navigate = useNavigate()
  const { catalog, catalogClient, chatPlanner, agentsClient, intentClient, boardStore, company } = useRouteContext({ from: '/ai' })
  const [messages, setMessages] = useState<Message[]>([])
  const [text, setText] = useState('')
  const [building, setBuilding] = useState(false)
  const [busy, setBusy] = useState(false)
  const [remembered, setRemembered] = useState<AgentContext | null>(null)
  const [board, setBoard] = useState<ChatBoard | null>(null)
  const [saving, setSaving] = useState(false)
  const bottom = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (bottom.current) bottom.current.scrollTop = bottom.current.scrollHeight
  }, [messages, busy])

  const send = async (message: string) => {
    const asked = message.trim()
    if (!asked || busy) return
    setBusy(true)
    setText('')
    setMessages((all) => [...all, { from: 'you', text: asked }])
    const forBoard = asked.toLowerCase().startsWith(BUILDER)
    const reply: IntentReply | null | 'figures_down' = forBoard ? null : await intentClient.answer(asked, company).catch((error) => (error instanceof IntentDataUnavailable ? 'figures_down' : null))
    if (reply === 'figures_down') {
      setMessages((all) => [...all, { from: 'ai', text: NO_FIGURES }])
      setBusy(false)
      return
    }
    const intent = reply?.reading ?? null
    if (reply && reply.problem === null && reply.answers.length > 0) {
      setMessages((all) => [...all, { from: 'ai', text: '', blocks: reply.answers.flatMap((item) => item.blocks), intent }])
      setBusy(false)
      return
    }
    if (reply?.reason === 'period_not_supported') {
      setMessages((all) => [...all, { from: 'ai', text: unusablePeriod(reply.periods), intent }])
      setBusy(false)
      return
    }
    const agent = forBoard ? null : await agentsClient.ask(asked, remembered ?? undefined).catch(() => undefined)
    if (agent === undefined) {
      setMessages((all) => [...all, { from: 'ai', text: UNAVAILABLE, intent }])
      setBusy(false)
      return
    }
    if (agent?.readable && agent.question) setRemembered(agent.question)
    if (agent && (agent.readable || (agent.problem !== null && SHOWN_PROBLEMS.includes(agent.problem)))) {
      setMessages((all) => [...all, { from: 'ai', text: '', agent, intent }])
      setBusy(false)
      return
    }
    const answer = await chatPlanner.plan(asked, catalog)
    if (agent && answer.catalogIds.length === 0 && !answer.board) {
      setMessages((all) => [...all, { from: 'ai', text: '', agent, intent }])
      setBusy(false)
      return
    }
    setMessages((all) => [...all, { from: 'ai', text: answer.reply, catalogIds: answer.catalogIds, board: answer.board, intent }])
    if (answer.board) setBoard(answer.board)
    setBusy(false)
  }

  const submit = (event: SyntheticEvent) => {
    event.preventDefault()
    send(building ? `${BUILDER} ${text}` : text)
    setBuilding(false)
  }

  const type = (value: string) => {
    if (!building && value.toLowerCase().startsWith(`${BUILDER} `)) {
      setBuilding(true)
      setText(value.slice(BUILDER.length + 1))
    } else setText(value)
  }

  return (
    <div className={classes.aiPage}>
      <PageHeader
        title="AI Mode"
        actions={
          <Button variant="default" leftSection={<ArrowLeftIcon size={16} />} onClick={() => navigate({ to: '/' })}>
            Back to boards
          </Button>
        }
      />
      <div className={classes.thread}>
        <div className={classes.messages} ref={bottom}>
          {messages.length === 0 && (
            <Stack align="center" gap="sm" ta="center" py="xl">
              <SparkleIcon size={36} weight="duotone" />
              <Title order={4}>Ask for what you want to see</Title>
              <Text c="dimmed" size="sm">
                Ask a question and the answer comes back with its charts. Start with {BUILDER} to build a whole board.
              </Text>
              {examples.map((example) => (
                <Button key={example} variant="light" size="xs" onClick={() => send(example)}>
                  {example}
                </Button>
              ))}
            </Stack>
          )}
          {messages.map((message, index) => (
            <div key={index} className={classes.bubble} data-from={message.from} data-wide={message.catalogIds?.length || message.agent?.blocks.length || message.blocks?.length ? true : undefined}>
              {message.from === 'you' && message.text.toLowerCase().startsWith(BUILDER) ? (
                <>
                  <span className={classes.mention}>{message.text.slice(0, BUILDER.length)}</span>
                  {message.text.slice(BUILDER.length)}
                </>
              ) : message.blocks ? (
                <AnswerBlocks blocks={message.blocks} label={null} />
              ) : message.agent ? (
                <AnswerBlocks blocks={message.agent.blocks} label={message.agent.label} />
              ) : (
                message.text
              )}
              {message.catalogIds && message.catalogIds.length > 0 && (
                <WidgetGrid>
                  {message.catalogIds.map((id) => {
                    const entry = catalog.find((candidate) => candidate.id === id)
                    return (
                      entry && (
                        <WidgetCell key={id} widget={entry.widget}>
                          <CatalogWidget entry={entry} client={catalogClient} company={company} />
                        </WidgetCell>
                      )
                    )
                  })}
                </WidgetGrid>
              )}
              {message.board && (
                <Button mt="xs" size="xs" variant="light" onClick={() => setBoard(message.board ?? null)}>
                  Open board
                </Button>
              )}
              {message.intent && <IntentCard reading={message.intent} answered={Boolean(message.catalogIds?.length || message.board || message.agent?.readable)} />}
            </div>
          ))}
          {busy && (
            <div className={classes.bubble} data-from="ai">
              Thinking…
            </div>
          )}
        </div>
        <form className={classes.chat} onSubmit={submit}>
          <Group wrap="nowrap">
            <TextInput
              flex={1}
              size="lg"
              radius="xl"
              aria-label="Message"
              placeholder={building ? 'What should the board show?' : `Ask the AI, or start with ${BUILDER} to build a board`}
              value={text}
              leftSection={building ? <Badge variant="light" size="lg" tt="none">{BUILDER}</Badge> : undefined}
              leftSectionWidth={building ? 104 : undefined}
              leftSectionPointerEvents="none"
              onChange={(event) => type(event.currentTarget.value)}
              onKeyDown={(event) => {
                if (event.key === 'Backspace' && building && text === '') setBuilding(false)
              }}
            />
            <ActionIcon type="submit" size={48} radius="xl" aria-label="Send" loading={busy} disabled={!text.trim() && !building}>
              <PaperPlaneRightIcon size={18} />
            </ActionIcon>
          </Group>
        </form>
      </div>
      <Modal opened={board !== null} onClose={() => setBoard(null)} title={
          <Group justify="space-between" pr="md">
            {board?.name}
            <Button size="xs" onClick={() => setSaving(true)}>
              Save as board
            </Button>
          </Group>
        }
        size="90%"
        closeButtonProps={{ 'aria-label': 'Close' }}
      >
        {board && <BoardGrid widgets={buildWidgets(board.catalogIds, catalog)} catalog={catalog} client={catalogClient} company={company} editing={false} onChange={() => undefined} />}
      </Modal>
      {board && (
        <SaveBoardModal
          opened={saving}
          onClose={() => setSaving(false)}
          store={boardStore}
          name={board.name}
          widgets={buildWidgets(board.catalogIds, catalog)}
          onSaved={(id) => navigate({ to: '/', search: { board: id } })}
        />
      )}
    </div>
  )
}
