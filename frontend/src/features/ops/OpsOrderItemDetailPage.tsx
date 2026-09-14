import { useParams } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { PriorityBadge } from '../../components/ui/PriorityBadge'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { Tag } from '../../components/ui/Tag'
import { DetailList } from '../../components/data/DetailList'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
  TableRowLink,
} from '../../components/data/Table'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { Page } from '../../components/layout/Page'
import { PageHeader } from '../../components/layout/PageHeader'
import { Section } from '../../components/layout/Section'
import { InternalCommentsPanel } from '../support/InternalCommentsPanel'
import { CONVERSATION_REASON_LABELS } from '../conversations/reasons'
import { formatCurrencyBRL, formatDate, formatDateTime } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import type { ConversationReason } from '../../types/conversation'
import { fetchOpsItemConversations, fetchOpsOrderItem } from './api'

export function OpsOrderItemDetailPage() {
  const { itemId } = useParams<{ itemId: string }>()

  const state = useAsync(async () => {
    const [item, conversations] = await Promise.all([
      fetchOpsOrderItem(itemId!),
      fetchOpsItemConversations(itemId!),
    ])
    return { item, conversations }
  }, [itemId])

  if (state.status === 'loading') {
    return <Spinner label="Carregando item..." />
  }
  if (state.status === 'error') {
    return <ErrorState message={state.error} onRetry={state.retry} />
  }

  const { item, conversations } = state.data

  return (
    <Page width="wide">
      <PageHeader
        title={item.product.name}
        subtitle={item.product.description ?? undefined}
        meta={<StatusBadge status={item.status} />}
        breadcrumbs={[{ label: 'Pedidos', to: '/ops/order-items' }, { label: item.product.name }]}
      />

      <Card>
        <DetailList
          entries={[
            { term: 'Vendedor', value: item.seller.name },
            { term: 'Comprador', value: item.buyer.name },
            { term: 'Quantidade', value: item.quantity },
            { term: 'Preço', value: formatCurrencyBRL(item.purchase_price) },
            {
              term: 'Pedido',
              value: `#${item.order.id.slice(0, 8)} — ${formatDate(item.order.created_at)}`,
            },
          ]}
        />
      </Card>

      <Section
        title="Conversas"
        description="Conteúdo da conversa com o Buyer não é visível para Ops."
      >
        {conversations.length === 0 ? (
          <EmptyState title="Nenhuma conversa neste item." />
        ) : (
          <Table caption="Conversas abertas e encerradas deste item">
            <TableHead>
              <TableRow>
                <TableHeaderCell>Motivo</TableHeaderCell>
                <TableHeaderCell>Situação</TableHeaderCell>
                <TableHeaderCell>Prioridade</TableHeaderCell>
                <TableHeaderCell>Última interação</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {conversations.map((conversation) => {
                const reasonLabel =
                  CONVERSATION_REASON_LABELS[conversation.reason as ConversationReason]
                return (
                  <TableRow key={conversation.id} linked>
                    <TableCell label="Motivo">
                      <TableRowLink to={`/ops/conversations/${conversation.id}`}>
                        {reasonLabel ?? conversation.reason}
                      </TableRowLink>
                    </TableCell>
                    <TableCell label="Situação">
                      <Tag tone={conversation.status === 'open' ? 'info' : 'muted'} dot>
                        {conversation.status === 'open' ? 'Aberta' : 'Encerrada'}
                      </Tag>
                    </TableCell>
                    <TableCell label="Prioridade">
                      <PriorityBadge priority={conversation.effective_priority} />
                    </TableCell>
                    <TableCell label="Última interação">
                      {formatDateTime(conversation.last_interaction_at)}
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        )}
      </Section>

      <InternalCommentsPanel itemId={item.id} viewerRole="ops" />
    </Page>
  )
}
