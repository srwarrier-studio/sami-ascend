import { useState } from 'react'
import type { ReactNode } from 'react'
import { TextInput } from '@mantine/core'
import classes from './PageHeader.module.css'

type PageHeaderProps = {
  title: string
  breadcrumb?: string[]
  actions?: ReactNode
  editing?: boolean
  onTitleChange?: (title: string) => void
}

function TitleField({ title, onTitleChange }: { title: string; onTitleChange: (title: string) => void }) {
  const [value, setValue] = useState(title)
  const [cancelled, setCancelled] = useState(false)
  const save = () => {
    const next = value.trim()
    if (!cancelled && next && next !== title) onTitleChange(next)
    else setValue(title)
    setCancelled(false)
  }
  return (
    <TextInput
      classNames={{ input: classes.titleInput }}
      aria-label="Board title"
      value={value}
      onChange={(event) => setValue(event.currentTarget.value)}
      onBlur={save}
      onKeyDown={(event) => {
        if (event.key === 'Enter') event.currentTarget.blur()
        if (event.key === 'Escape') {
          setCancelled(true)
          event.currentTarget.blur()
        }
      }}
    />
  )
}

export function PageHeader({ title, breadcrumb = [], actions, editing = false, onTitleChange }: PageHeaderProps) {
  return (
    <header className={classes.header}>
      <div>
        {breadcrumb.length > 0 && (
          <div className={classes.crumbs}>
            {breadcrumb.map((crumb, index) => (
              <span key={crumb}>
                {index > 0 && '/ '}
                {crumb}
              </span>
            ))}
          </div>
        )}
        {editing && onTitleChange ? (
          <TitleField key={title} title={title} onTitleChange={onTitleChange} />
        ) : (
          <h1 className={classes.title}>{title}</h1>
        )}
      </div>
      {actions}
    </header>
  )
}
