import { Link } from 'react-router-dom'
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
import type { SellerDashboard } from '../../types/dashboard'
import type { OrderItemStatus } from '../../types/order'
import { ORDER_ITEM_STATUS_LABELS } from '../orders/status'
import { SummaryGrid, SummaryStat } from './SummaryStat'

const STATUS_KEYS: OrderItemStatus[] = [
  'placed',
  'preparing',
  'in_transit',
  'delivered',
  'cancelled',
]

export function SellerDashboardView({ data }: { data: SellerDashboard }) {
  const { summary, attention, recent } = data

  return (
    <Page width="wide">
      <PageHeader title="Início" subtitle="O estado da sua operação agora." />

      <Section title="Resumo">
        <SummaryGrid>
          <SummaryStat label="Total" value={summary.total_order_items} to="/seller/orders" />
          <SummaryStat label="Ativos" value={summary.active_order_items} to="/seller/orders" />
          {STATUS_KEYS.map((status) => (
            <SummaryStat
              key={status}
              label={ORDER_ITEM_STATUS_LABELS[status]}
              value={summary.order_items_by_status[status]}
              to={`/seller/orders?status=${status}`}
            />
          ))}
        </SummaryGrid>
      </Section>

      <Section title="Atenção">
        {attention.open_conversations === 0 ? (
          <EmptyState title="Nenhuma conversa em aberto." />
        ) : (
          <Link to="/seller/orders">
            {attention.open_conversations}{' '}
            {attention.open_conversations === 1 ? 'conversa em aberto' : 'conversas em aberto'}
          </Link>
        )}
      </Section>

      <Section
        title="Recentes"
        action={
          recent.order_items.length > 0 ? <Link to="/seller/orders">Ver todos</Link> : undefined
        }
      >
        {recent.order_items.length === 0 ? (
          <EmptyState
            title="Nenhum pedido na sua operação."
            description="Publique uma oferta para começar a vender."
            action={<Link to="/catalog">Ir ao catálogo</Link>}
          />
        ) : (
          <Table caption="Itens de pedido mais recentes">
            <TableHead>
              <TableRow>
                <TableHeaderCell>Pedido</TableHeaderCell>
                <TableHeaderCell>Produto</TableHeaderCell>
                <TableHeaderCell>Comprador</TableHeaderCell>
                <TableHeaderCell numeric>Qtd</TableHeaderCell>
                <TableHeaderCell numeric>Valor</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Data</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {recent.order_items.map((item) => (
                <TableRow key={item.order_item_id} linked>
                  <TableCell label="Pedido">{formatOrderItemNumber(item.number)}</TableCell>
                  <TableCell label="Produto">
                    <TableRowLink to={`/seller/orders/${item.order_item_id}`}>
                      {item.product.name}
                    </TableRowLink>
                  </TableCell>
                  <TableCell label="Comprador">{item.buyer.name}</TableCell>
                  <TableCell label="Qtd" numeric>
                    {item.quantity}
                  </TableCell>
                  <TableCell label="Valor" numeric>
                    {formatCurrencyBRL(item.purchase_price)}
                  </TableCell>
                  <TableCell label="Status">
                    <StatusBadge status={item.status} />
                  </TableCell>
                  <TableCell label="Data">{formatDateTime(item.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Section>
    </Page>
  )
}
