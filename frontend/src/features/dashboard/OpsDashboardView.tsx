import { Link } from 'react-router-dom'
import { PriorityBadge } from '../../components/ui/PriorityBadge'
import { StatusBadge } from '../../components/ui/StatusBadge'
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
import { Page } from '../../components/layout/Page'
import { PageHeader } from '../../components/layout/PageHeader'
import { Section } from '../../components/layout/Section'
import { formatCurrencyBRL, formatDateTime } from '../../lib/utils/format'
import { formatOrderItemNumber } from '../../lib/utils/orderNumber'
import type { EffectivePriority } from '../../types/conversation'
import type { OpsDashboard } from '../../types/dashboard'
import { PRIORITY_LABELS } from '../ops/priority'
import { SummaryGrid, SummaryStat } from './SummaryStat'

const PRIORITY_KEYS: EffectivePriority[] = ['critical', 'high', 'medium', 'low']

export function OpsDashboardView({ data }: { data: OpsDashboard }) {
  const { summary, attention } = data
  const preview = attention.priority_queue_preview

  return (
    <Page width="wide">
      <PageHeader title="Início" subtitle="A fila de atendimento de relance." />

      <Section title="Resumo">
        <SummaryGrid>
          <SummaryStat
            label="Conversas abertas"
            value={summary.open_conversations}
            to="/ops/queue"
          />
          {PRIORITY_KEYS.map((priority) => (
            <SummaryStat
              key={priority}
              label={PRIORITY_LABELS[priority]}
              value={summary.conversations_by_priority[priority]}
              to={`/ops/queue?effective_priority=${priority}`}
              accent={priority === 'critical'}
            />
          ))}
        </SummaryGrid>
      </Section>

      <Section
        title="Atenção"
        action={preview.length > 0 ? <Link to="/ops/queue">Ver fila completa</Link> : undefined}
      >
        {preview.length === 0 ? (
          <EmptyState title="Nenhuma conversa em aberto." />
        ) : (
          <Table caption="Conversas mais urgentes da fila">
            <TableHead>
              <TableRow>
                <TableHeaderCell>Prioridade</TableHeaderCell>
                <TableHeaderCell>Pedido</TableHeaderCell>
                <TableHeaderCell>Produto</TableHeaderCell>
                <TableHeaderCell>Vendedor</TableHeaderCell>
                <TableHeaderCell>Comprador</TableHeaderCell>
                <TableHeaderCell numeric>Valor</TableHeaderCell>
                <TableHeaderCell>Status do item</TableHeaderCell>
                <TableHeaderCell>Última interação</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {preview.map((item) => (
                <TableRow key={item.conversation_id} linked>
                  <TableCell label="Prioridade">
                    <PriorityBadge priority={item.effective_priority} />
                  </TableCell>
                  <TableCell label="Pedido">{formatOrderItemNumber(item.number)}</TableCell>
                  <TableCell label="Produto">
                    <TableRowLink to={`/ops/conversations/${item.conversation_id}`}>
                      {item.product.name}
                    </TableRowLink>
                  </TableCell>
                  <TableCell label="Vendedor">{item.seller.name}</TableCell>
                  <TableCell label="Comprador">{item.buyer.name}</TableCell>
                  <TableCell label="Valor" numeric>
                    {formatCurrencyBRL(item.purchase_price)}
                  </TableCell>
                  <TableCell label="Status do item">
                    <StatusBadge status={item.order_item_status} />
                  </TableCell>
                  <TableCell label="Última interação">
                    {formatDateTime(item.last_interaction_at)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Section>
    </Page>
  )
}
