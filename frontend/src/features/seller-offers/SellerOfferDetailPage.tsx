import { useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Checkbox } from '../../components/ui/Checkbox'
import { TextAreaField } from '../../components/ui/TextAreaField'
import { TextField } from '../../components/ui/TextField'
import { ErrorState } from '../../components/feedback/ErrorState'
import { FormError } from '../../components/feedback/FormError'
import { Spinner } from '../../components/feedback/Spinner'
import { Page } from '../../components/layout/Page'
import { PageHeader } from '../../components/layout/PageHeader'
import { Section } from '../../components/layout/Section'
import { ConfirmDialog } from '../../components/overlay/ConfirmDialog'
import { useToast } from '../../components/overlay/toast-context'
import { useAuth } from '../../app/providers/auth-context'
import { errorMessage } from '../../lib/utils/errorMessage'
import { useAsync } from '../../lib/utils/useAsync'
import type { Offer, Product } from '../../types/catalog'
import {
  deleteOffer,
  deleteProduct,
  fetchOffer,
  fetchProduct,
  updateOffer,
  updateProduct,
} from '../catalog/api'
import { toApiPrice } from './price'
import styles from './SellerOfferForm.module.css'

export function SellerOfferDetailPage() {
  const { offerId } = useParams<{ offerId: string }>()
  const { user } = useAuth()

  const state = useAsync(async () => {
    const offer = await fetchOffer(offerId!)
    const product = await fetchProduct(offer.product_id)
    return { offer, product }
  }, [offerId])

  if (state.status === 'loading') {
    return <Spinner label="Carregando oferta..." />
  }
  if (state.status === 'error') {
    return <ErrorState message={state.error} onRetry={state.retry} />
  }

  const { offer, product } = state.data
  if (user?.seller_id && offer.seller_id !== user.seller_id) {
    return <ErrorState message="Esta oferta não pertence à sua loja." />
  }

  return (
    <SellerOfferEditor
      key={`${offer.id}-${offer.price}-${offer.stock}-${String(offer.available)}-${product.name}`}
      offer={offer}
      product={product}
      onSaved={state.retry}
    />
  )
}

type PendingDelete = 'offer' | 'product' | null

function SellerOfferEditor({
  offer,
  product,
  onSaved,
}: {
  offer: Offer
  product: Product
  onSaved: () => void
}) {
  const navigate = useNavigate()
  const { showToast } = useToast()
  const [price, setPrice] = useState(offer.price)
  const [stock, setStock] = useState(String(offer.stock))
  const [available, setAvailable] = useState(offer.available)
  const [productName, setProductName] = useState(product.name)
  const [productDescription, setProductDescription] = useState(product.description ?? '')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [confirmingDelete, setConfirmingDelete] = useState<PendingDelete>(null)

  async function handleSaveOffer(event: FormEvent) {
    event.preventDefault()
    const apiPrice = toApiPrice(price)
    const stockValue = Number(stock)
    if (!apiPrice) {
      setError('Informe um preço válido (ex.: 10.00).')
      return
    }
    if (!Number.isInteger(stockValue) || stockValue < 0) {
      setError('Informe um estoque inteiro maior ou igual a zero.')
      return
    }
    setPending(true)
    setError(null)
    try {
      await updateOffer(offer.id, { price: apiPrice, stock: stockValue, available })
      showToast({ message: 'Oferta atualizada.' })
      onSaved()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setPending(false)
    }
  }

  async function handleSaveProduct(event: FormEvent) {
    event.preventDefault()
    setPending(true)
    setError(null)
    try {
      await updateProduct(product.id, {
        name: productName.trim(),
        description: productDescription.trim() || null,
      })
      showToast({ message: 'Produto atualizado.' })
      onSaved()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setPending(false)
    }
  }

  async function handleConfirmDelete() {
    const target = confirmingDelete
    if (!target) {
      return
    }
    setPending(true)
    setError(null)
    try {
      await (target === 'offer' ? deleteOffer(offer.id) : deleteProduct(product.id))
      showToast({ message: target === 'offer' ? 'Oferta excluída.' : 'Produto excluído.' })
      navigate('/seller/offers')
    } catch (err) {
      setError(errorMessage(err))
      setConfirmingDelete(null)
    } finally {
      setPending(false)
    }
  }

  return (
    <Page>
      <PageHeader
        title={product.name}
        subtitle="Preço, estoque e dados do produto na vitrine."
        breadcrumbs={[{ label: 'Minhas ofertas', to: '/seller/offers' }, { label: product.name }]}
      />

      <FormError message={error} />

      <Card>
        <Section title="Preço e estoque">
          <form className={styles.form} onSubmit={handleSaveOffer}>
            <TextField
              label="Preço"
              name="price"
              value={price}
              onChange={(event) => setPrice(event.target.value)}
              hint="Use ponto como separador decimal."
              required
            />
            <TextField
              label="Estoque"
              name="stock"
              type="number"
              min={0}
              value={stock}
              onChange={(event) => setStock(event.target.value)}
              required
            />
            <Checkbox
              label="Disponível para compra"
              name="available"
              checked={available}
              onChange={(event) => setAvailable(event.target.checked)}
            />
            <Button type="submit" loading={pending}>
              Salvar oferta
            </Button>
          </form>
        </Section>
      </Card>

      <Card>
        <Section
          title="Produto da vitrine"
          description="O produto é compartilhado no catálogo. Alterar o nome ou a descrição vale para todas as lojas que o ofertam."
        >
          <form className={styles.form} onSubmit={handleSaveProduct}>
            <TextField
              label="Nome"
              name="productName"
              value={productName}
              onChange={(event) => setProductName(event.target.value)}
              required
              maxLength={200}
            />
            <TextAreaField
              label="Descrição"
              name="productDescription"
              value={productDescription}
              onChange={(event) => setProductDescription(event.target.value)}
              maxLength={2000}
            />
            <Button type="submit" loading={pending}>
              Salvar produto
            </Button>
          </form>
        </Section>
      </Card>

      <Card>
        <Section title="Excluir">
          <div className={styles.danger}>
            <Button
              type="button"
              variant="destructive"
              disabled={pending}
              onClick={() => setConfirmingDelete('offer')}
            >
              Excluir oferta
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={pending}
              onClick={() => setConfirmingDelete('product')}
            >
              Excluir produto
            </Button>
          </div>
        </Section>
      </Card>

      <ConfirmDialog
        open={confirmingDelete !== null}
        title={
          confirmingDelete === 'product' ? 'Excluir o produto da vitrine?' : 'Excluir esta oferta?'
        }
        description={
          confirmingDelete === 'product'
            ? 'Só funciona se nenhuma loja tiver oferta ativa para ele.'
            : 'A oferta sai do catálogo. Pedidos já feitos não são afetados.'
        }
        confirmLabel="Confirmar exclusão"
        destructive
        pending={pending}
        onConfirm={handleConfirmDelete}
        onCancel={() => setConfirmingDelete(null)}
      />
    </Page>
  )
}
