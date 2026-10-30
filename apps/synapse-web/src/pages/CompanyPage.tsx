import { useNavigate, useRouteContext } from '@tanstack/react-router'
import { Card, SimpleGrid, Text, Title } from '@sami/ui'
import { CompanyLogo } from '../session/CompanyLogo'
import { findCompany } from '../session/companies'
import classes from './Company.module.css'

export function CompanyPage() {
  const { session, setCompany } = useRouteContext({ from: '/company' })
  const navigate = useNavigate()
  if (session.status !== 'signedIn') return null

  const choose = (id: string) => {
    setCompany(id)
    navigate({ to: '/', search: { board: undefined } })
  }

  return (
    <div className={classes.page}>
      <Title order={2}>Choose a company</Title>
      <SimpleGrid className={classes.grid} cols={{ base: 1, sm: Math.min(session.user.companies.length, 3) }}>
        {session.user.companies.map((id) => (
          <Card key={id} component="button" type="button" withBorder shadow="sm" padding="xl" className={classes.card} onClick={() => choose(id)}>
            <CompanyLogo id={id} size={72} />
            <Text fw={500}>{findCompany(id)?.name}</Text>
          </Card>
        ))}
      </SimpleGrid>
    </div>
  )
}
