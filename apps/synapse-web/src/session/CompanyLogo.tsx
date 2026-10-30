import { Avatar } from '@sami/ui'
import { findCompany } from './companies'

export function CompanyLogo({ id, size = 32 }: { id: string; size?: number }) {
  const company = findCompany(id)
  if (!company) return null
  return (
    <Avatar aria-hidden color={company.color} variant="filled" radius={0} size={size}>
      {company.logoLetter}
    </Avatar>
  )
}
