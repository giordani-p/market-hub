import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Checkbox, Radio } from '../../components/ui/Checkbox'
import { SelectField } from '../../components/ui/SelectField'
import { TextAreaField } from '../../components/ui/TextAreaField'
import { TextField } from '../../components/ui/TextField'
import { ErrorState } from '../../components/feedback/ErrorState'
import { FormError } from '../../components/feedback/FormError'
import { Spinner } from '../../components/feedback/Spinner'
import { Page } from '../../components/layout/Page'
import { PageHeader } from '../../components/layout/PageHeader'
import { useToast } from '../../components/overlay/toast-context'
import { errorMessage } from '../../lib/utils/errorMessage'
import { useAsync } from '../../lib/utils/useAsync'
import { createOffer, createProduct, fetchProducts } from '../catalog/api'
import { toApiPrice } from './price'
import styles from './SellerOfferForm.module.css'

export function SellerOfferNewPage() {
  const navigate = useNavigate()
  const { showToast } = useToast()
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
      showToast({ message: 'Oferta publicada.' })
      navigate(`/seller/offers/${offer.id}`)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setPending(false)
    }
  }

  return (
    <Page>
      <PageHeader
        title="Nova oferta"
        breadcrumbs={[{ label: 'Minhas ofertas', to: '/seller/offers' }, { label: 'Nova oferta' }]}
      />

      <Card>
        <form className={styles.form} onSubmit={handleSubmit}>
          <fieldset className={styles.modeGroup}>
            <legend className={styles.legend}>Produto</legend>
            <Radio
              label="Usar produto existente"
              name="mode"
              checked={mode === 'existing'}
              onChange={() => setMode('existing')}
            />
            <Radio
              label="Cadastrar novo produto"
              name="mode"
              checked={mode === 'new'}
              onChange={() => setMode('new')}
            />
          </fieldset>

          {mode === 'existing' ? (
            <SelectField
              label="Produto da vitrine"
              name="productId"
              value={productId}
              onChange={(event) => setProductId(event.target.value)}
              required
              options={[
                { value: '', label: 'Selecione' },
                ...products.map((product) => ({ value: product.id, label: product.name })),
              ]}
            />
          ) : (
            <>
              <TextField
                label="Nome do produto"
                name="productName"
                value={productName}
                onChange={(event) => setProductName(event.target.value)}
                required
                maxLength={200}
              />
              <TextAreaField
                label="Descrição (opcional)"
                name="productDescription"
                value={productDescription}
                onChange={(event) => setProductDescription(event.target.value)}
                maxLength={2000}
              />
            </>
          )}

          <TextField
            label="Preço"
            name="price"
            value={price}
            onChange={(event) => setPrice(event.target.value)}
            placeholder="10.00"
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

          <FormError message={error} />

          <Button type="submit" loading={pending}>
            Publicar oferta
          </Button>
        </form>
      </Card>
    </Page>
  )
}
