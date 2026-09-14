import { Link } from 'react-router-dom'
import { EmptyState } from '../../components/feedback/EmptyState'
import { Page } from '../../components/layout/Page'

export function NotFoundPage() {
  return (
    <Page width="narrow">
      <EmptyState
        title="Página não encontrada."
        description="O endereço acessado não existe ou saiu do ar."
        action={<Link to="/">Voltar ao início</Link>}
      />
    </Page>
  )
}
