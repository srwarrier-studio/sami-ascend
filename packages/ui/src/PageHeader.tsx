import type { ReactNode } from 'react'
import classes from './PageHeader.module.css'

type PageHeaderProps = {
  title: string
  breadcrumb?: string[]
  actions?: ReactNode
}

export function PageHeader({ title, breadcrumb = [], actions }: PageHeaderProps) {
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
        <h1 className={classes.title}>{title}</h1>
      </div>
      {actions}
    </header>
  )
}
