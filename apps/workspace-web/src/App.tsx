import { Loader, Text } from '@sami/ui'
import { authClient } from './api/auth'
import { useSession } from './session/useSession'

export default function App() {
  const { session } = useSession(authClient)
  if (session.status === 'loading') return <Loader />
  return <Text>{session.status}</Text>
}
