import { Plus } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '../../components/ui/Button'
import { Tag } from '../../components/ui/Tag'
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
import { SkeletonList } from '../../components/ui/Skeleton'
import { Page } from '../../components/layout/Page'
import { PageHeader } from '../../components/layout/PageHeader'
import { useAuth } from '../../app/providers/auth-context'
import { formatCurrencyBRL } from '../../lib/utils/format'
import { useAsync } from '../../lib/utils/useAsync'
import { fetchOffers, fetchProducts } from '../catalog/api'

export function SellerOffersListPage() {
  const { user } = useAuth()
  const sellerId = user?.seller_id

  const state = useAsync(async () => {
    if (!sellerId) {
      throw new Error('Seller sem loja associada.')
    }
    const [offers, products] = await Promise.all([fetchOffers(sellerId), fetchProducts()])
    const names = new Map(products.map((product) => [product.id, product.name]))
    return { offers, names }
  }, [sellerId])

  const newOfferAction = (
    <Link to="/seller/offers/new">
      <Button type="button">
        <Plus size={16} aria-hidden="true" />
        Nova oferta
      </Button>
    </Link>
  )

  return (
    <Page width="wide">
      <PageHeader
        title="Minhas ofertas"
        subtitle="Preço e estoque que a sua loja publica no catálogo."
        actions={newOfferAction}
      />

      {state.status === 'loading' && <SkeletonList variant="row" label="Carregando ofertas..." />}
      {state.status === 'error' && <ErrorState message={state.error} onRetry={state.retry} />}

      {state.status === 'success' && state.data.offers.length === 0 && (
        <EmptyState
          title="Você ainda não tem ofertas."
          description="Cadastre um produto da vitrine e publique preço e estoque."
          action={newOfferAction}
        />
      )}

      {state.status === 'success' && state.data.offers.length > 0 && (
        <Table caption="Ofertas publicadas pela sua loja">
          <TableHead>
            <TableRow>
              <TableHeaderCell>Produto</TableHeaderCell>
              <TableHeaderCell numeric>Preço</TableHeaderCell>
              <TableHeaderCell numeric>Estoque</TableHeaderCell>
              <TableHeaderCell>Disponível</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {state.data.offers.map((offer) => (
              <TableRow key={offer.id} linked>
                <TableCell label="Produto">
                  <TableRowLink to={`/seller/offers/${offer.id}`}>
                    {state.data.names.get(offer.product_id) ?? 'Produto'}
                  </TableRowLink>
                </TableCell>
                <TableCell label="Preço" numeric>
                  {formatCurrencyBRL(offer.price)}
                </TableCell>
                <TableCell label="Estoque" numeric>
                  {offer.stock}
                </TableCell>
                <TableCell label="Disponível">
                  <Tag tone={offer.available ? 'success' : 'muted'} dot>
                    {offer.available ? 'Disponível' : 'Indisponível'}
                  </Tag>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Page>
  )
}
