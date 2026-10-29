import { Alert as MantineAlert } from '@mantine/core'
import type { AlertProps } from '@mantine/core'
import { CheckCircleIcon, InfoIcon, WarningCircleIcon, WarningIcon } from '@phosphor-icons/react'
import type { ReactNode } from 'react'

const icons: Record<string, ReactNode> = {
  blue: <InfoIcon size={18} />,
  green: <CheckCircleIcon size={18} />,
  yellow: <WarningIcon size={18} />,
  red: <WarningCircleIcon size={18} />,
}

export function Alert({ color = 'blue', icon, ...rest }: AlertProps) {
  return <MantineAlert color={color} icon={icon ?? icons[color]} {...rest} />
}
