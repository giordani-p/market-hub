import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { ErrorState } from '../../components/feedback/ErrorState'
import { Spinner } from '../../components/feedback/Spinner'
import { errorMessage } from '../../lib/utils/errorMessage'
import { useAsync } from '../../lib/utils/useAsync'
import { createOffer, createProduct, fetchProducts } from '../catalog/api'
import { toApiPrice } from './price'

export function SellerOfferNewPage() {
  const navigate = useNavigate()
  const productsState = useAsync(fetchProducts, [])
  const [mode, setMode] = useState<'existing' | 'new'>('existing')
  const [productId, setProductId] = useState('')
  const [productName, setProductName] = useState('')
  const [productDescription, setProductDescription] = useState('')
  const [price, setPrice] = useState('')
  const [stock, setStock] = useState('1')
  const [available, setAvailable] = useState(true)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (productsState.status === 'loading') {
    return <Spinner label="Carregando produtos..." />
  }
  if (productsState.status === 'error') {
    return <ErrorState message={productsState.error} onRetry={productsState.retry} />
  }

  const products = productsState.data

  async function handleSubmit(event: FormEvent) {
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
      let targetProductId = productId
      if (mode === 'new') {
        const product = await createProduct({
          name: productName.trim(),
          description: productDescription.trim() || null,
        })
        targetProductId = product.id
      }
      if (!targetProductId) {
        setError('Selecione ou cadastre um produto.')
        return
      }
      const offer = await createOffer({
        product_id: targetProductId,
        price: apiPrice,
        stock: stockValue,
        available,
      })
      navigate(`/seller/offers/${offer.id}`)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="page">
      <h1>Nova oferta</h1>
      <form className="form-stack" onSubmit={handleSubmit}>
        <fieldset className="offer-mode">
          <legend>Produto</legend>
          <label className="checkbox-field">
            <input
              type="radio"
              name="mode"
              checked={mode === 'existing'}
              onChange={() => setMode('existing')}
            />
            Usar produto existente
          </label>
          <label className="checkbox-field">
            <input
              type="radio"
              name="mode"
              checked={mode === 'new'}
              onChange={() => setMode('new')}
            />
            Cadastrar novo produto
          </label>
        </fieldset>

        {mode === 'existing' ? (
          <label className="field">
            <span>Produto da vitrine</span>
            <select
              className="input"
              value={productId}
              onChange={(event) => setProductId(event.target.value)}
              required
            >
              <option value="">Selecione</option>
              {products.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.name}
                </option>
              ))}
            </select>
          </label>
        ) : (
          <>
            <Input
              label="Nome do produto"
              name="productName"
              value={productName}
              onChange={(event) => setProductName(event.target.value)}
              required
              maxLength={200}
            />
            <label className="field">
              <span>Descrição (opcional)</span>
              <textarea
                className="input"
                name="productDescription"
                value={productDescription}
                onChange={(event) => setProductDescription(event.target.value)}
                maxLength={2000}
                rows={3}
              />
            </label>
          </>
        )}

        <Input
          label="Preço"
          name="price"
          value={price}
          onChange={(event) => setPrice(event.target.value)}
          placeholder="10.00"
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

        {error && (
          <p className="field-error" role="alert">
            {error}
          </p>
        )}

        <Button type="submit" disabled={pending}>
          {pending ? 'Salvando...' : 'Publicar oferta'}
        </Button>
      </form>
    </div>
  )
}
