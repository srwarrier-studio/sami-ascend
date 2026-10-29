import type { ReactNode } from 'react'
import { Link } from '@tanstack/react-router'
import { AppFrame, SquaresFourIcon } from '@sami/ui'
import type { User } from './session/sessionClient'

type ShellProps = { user: User; onLogout: () => void; children: ReactNode }

export function Shell({ user, onLogout, children }: ShellProps) {
  return (
    <AppFrame
      layout="top"
      brand={{ name: 'Synapse', subtitle: 'Management' }}
      user={{ name: user.name, email: user.email }}
      onSignOut={onLogout}
      navGroups={[
        [
          {
            key: 'boards',
            label: 'My boards',
            icon: SquaresFourIcon,
            active: true,
            render: ({ className, children: content }) => (
              <Link to="/" className={className} data-active>
                {content}
              </Link>
            ),
          },
        ],
      ]}
    >
      {children}
    </AppFrame>
  )
}
