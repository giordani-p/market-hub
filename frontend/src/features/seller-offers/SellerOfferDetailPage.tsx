import { useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
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
  const [price, setPrice] = useState(offer.price)
  const [stock, setStock] = useState(String(offer.stock))
  const [available, setAvailable] = useState(offer.available)
  const [productName, setProductName] = useState(product.name)
  const [productDescription, setProductDescription] = useState(product.description ?? '')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [confirmOfferDelete, setConfirmOfferDelete] = useState(false)
  const [confirmProductDelete, setConfirmProductDelete] = useState(false)

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
      onSaved()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setPending(false)
    }
  }

  async function handleDeleteOffer() {
    setPending(true)
    setError(null)
    try {
      await deleteOffer(offer.id)
      navigate('/seller/offers')
    } catch (err) {
      setError(errorMessage(err))
      setConfirmOfferDelete(false)
    } finally {
      setPending(false)
    }
  }

  async function handleDeleteProduct() {
    setPending(true)
    setError(null)
    try {
      await deleteProduct(product.id)
      navigate('/seller/offers')
    } catch (err) {
      setError(errorMessage(err))
      setConfirmProductDelete(false)
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="page">
      <h1>Oferta</h1>
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}

      <form className="form-stack" onSubmit={handleSaveOffer}>
        <h2>Preço e estoque</h2>
        <Input
          label="Preço"
          name="price"
          value={price}
          onChange={(event) => setPrice(event.target.value)}
          required
        />
        <Input
          label="Estoque"
          name="stock"
          type="number"
          min={0}
          value={stock}
          onChange={(event) => setStock(event.target.value)}
          required
        />
        <label className="checkbox-field">
          <input
            type="checkbox"
            name="available"
            checked={available}
            onChange={(event) => setAvailable(event.target.checked)}
          />
          Disponível para compra
        </label>
        <Button type="submit" disabled={pending}>
          {pending ? 'Salvando...' : 'Salvar oferta'}
        </Button>
      </form>

      <form className="form-stack" onSubmit={handleSaveProduct}>
        <h2>Produto da vitrine</h2>
        <p className="text-muted">
          O produto é compartilhado no catálogo. Alterar o nome ou a descrição vale para todas as
          lojas que o ofertam.
        </p>
        <Input
          label="Nome"
          name="productName"
          value={productName}
          onChange={(event) => setProductName(event.target.value)}
          required
          maxLength={200}
        />
        <label className="field">
          <span>Descrição</span>
          <textarea
            className="input"
            name="productDescription"
            value={productDescription}
            onChange={(event) => setProductDescription(event.target.value)}
            maxLength={2000}
            rows={3}
          />
        </label>
        <Button type="submit" disabled={pending}>
          {pending ? 'Salvando...' : 'Salvar produto'}
        </Button>
      </form>

      <div className="status-actions">
        <h2>Excluir</h2>
        {!confirmOfferDelete ? (
          <Button
            type="button"
            variant="destructive"
            disabled={pending}
            onClick={() => setConfirmOfferDelete(true)}
          >
            Excluir oferta
          </Button>
        ) : (
          <div className="confirm-inline">
            <span>Excluir esta oferta?</span>
            <Button
              type="button"
              variant="destructive"
              onClick={handleDeleteOffer}
              disabled={pending}
            >
              {pending ? 'Excluindo...' : 'Confirmar exclusão'}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setConfirmOfferDelete(false)}
              disabled={pending}
            >
              Voltar
            </Button>
          </div>
        )}

        {!confirmProductDelete ? (
          <Button
            type="button"
            variant="destructive"
            disabled={pending}
            onClick={() => setConfirmProductDelete(true)}
          >
            Excluir produto
          </Button>
        ) : (
          <div className="confirm-inline">
            <span>Excluir o produto da vitrine? Só funciona se não houver ofertas.</span>
            <Button
              type="button"
              variant="destructive"
              onClick={handleDeleteProduct}
              disabled={pending}
            >
              {pending ? 'Excluindo...' : 'Confirmar exclusão'}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setConfirmProductDelete(false)}
              disabled={pending}
            >
              Voltar
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
