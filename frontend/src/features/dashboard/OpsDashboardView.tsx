import { Link } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { PriorityBadge } from '../../components/ui/PriorityBadge'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { EmptyState } from '../../components/feedback/EmptyState'
import { formatCurrencyBRL, formatDateTime } from '../../lib/utils/format'
import type { EffectivePriority } from '../../types/conversation'
import type { OpsDashboard } from '../../types/dashboard'
import { PRIORITY_LABELS } from '../ops/priority'
import { SummaryStat } from './SummaryStat'

const PRIORITY_KEYS: EffectivePriority[] = ['critical', 'high', 'medium', 'low']

export function OpsDashboardView({ data }: { data: OpsDashboard }) {
  const { summary, attention } = data
  const preview = attention.priority_queue_preview

  return (
    <div className="page page-wide">
      <h1>Início</h1>

      <section className="dashboard-section">
        <h2>Resumo</h2>
        <div className="dashboard-summary">
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
        </div>
      </section>

      <section className="dashboard-section">
        <h2>Atenção</h2>
        {preview.length === 0 ? (
          <EmptyState title="Nenhuma conversa em aberto." />
        ) : (
          <>
            <div className="order-list">
              {preview.map((item) => (
                <Link
                  key={item.conversation_id}
                  to={`/ops/conversations/${item.conversation_id}`}
                  className="product-link"
                >
                  <Card>
                    <div className="order-item-row">
                      <span>{item.product.name}</span>
                      <span className="text-muted">{item.seller.name}</span>
                      <span className="text-muted">{item.buyer.name}</span>
                      <span>{formatCurrencyBRL(item.purchase_price)}</span>
                      <StatusBadge status={item.order_item_status} />
                      <PriorityBadge priority={item.effective_priority} />
                    </div>
                    <span className="text-muted">{formatDateTime(item.last_interaction_at)}</span>
                  </Card>
                </Link>
              ))}
            </div>
            <Link to="/ops/queue">Ver fila completa</Link>
          </>
        )}
      </section>
    </div>
  )
}
