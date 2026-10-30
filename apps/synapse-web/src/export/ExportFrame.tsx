import type { ReactNode, Ref } from 'react'
import { Group, Text, Title } from '@sami/ui'
import { companyBrand } from './companyBrand'
import classes from '../boards/Board.module.css'

type ExportFrameProps = {
  exporting: boolean
  userName: string
  generatedAt: Date
  frameRef?: Ref<HTMLDivElement>
  children: ReactNode
}

export function ExportFrame({ exporting, userName, generatedAt, frameRef, children }: ExportFrameProps) {
  return (
    <div ref={frameRef} className={classes.sheet}>
      <div hidden={!exporting} className={classes.sheetHeader}>
        <Group>
          <div className={classes.logo}>{companyBrand.logoLetter}</div>
          <Title order={2}>{companyBrand.name}</Title>
        </Group>
      </div>
      {children}
      <div hidden={!exporting} className={classes.sheetFooter}>
        <Text size="xs" c="dimmed">
          Generated {generatedAt.toLocaleString()} by {userName}
        </Text>
      </div>
    </div>
  )
}
