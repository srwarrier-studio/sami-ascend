import { useNavigate, useRouteContext } from '@tanstack/react-router'
import { Card, Container, Group, Stack, Text, Title } from '@sami/ui'
import { CompanyLogo } from '../session/CompanyLogo'
import { findCompany } from '../session/companies'

export function CompanyPage() {
  const { session, setCompany } = useRouteContext({ from: '/company' })
  const navigate = useNavigate()
  if (session.status !== 'signedIn') return null

  const choose = (id: string) => {
    setCompany(id)
    navigate({ to: '/', search: { board: undefined } })
  }

  return (
    <Container size="xs" py="xl">
      <Stack>
        <Title order={2}>Choose a company</Title>
        {session.user.companies.map((id) => (
          <Card key={id} component="button" type="button" withBorder onClick={() => choose(id)}>
            <Group>
              <CompanyLogo id={id} size={40} />
              <Text>{findCompany(id)?.name}</Text>
            </Group>
          </Card>
        ))}
      </Stack>
    </Container>
  )
}
