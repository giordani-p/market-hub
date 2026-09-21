import { useState } from 'react'
import { Button } from '../../components/ui/Button'
import { TextField } from '../../components/ui/TextField'
import { EmptyState } from '../../components/feedback/EmptyState'
import { checkoutRejectReasonLabel } from '../orders/checkoutErrors'
import { createOrder } from '../orders/api'
import { ApiRequestError } from '../../lib/api/client'
import { errorMessage } from '../../lib/utils/errorMessage'
import { formatCurrencyBRL } from '../../lib/utils/format'
import type { Offer } from '../../types/catalog'
import type { CheckoutRejectedBody, Order } from '../../types/order'
import styles from './PurchasePanel.module.css'

interface PurchasePanelProps {
  offers: Offer[]
  onPurchased: (order: Order) => void
}

function isCheckoutRejectedBody(details: unknown): details is CheckoutRejectedBody {
  return (
    typeof details === 'object' &&
    details !== null &&
    Array.isArray((details as CheckoutRejectedBody).items)
  )
}

export function PurchasePanel({ offers, onPurchased }: PurchasePanelProps) {
  const availableOffers = offers.filter((offer) => offer.available && offer.stock > 0)
  const [selectedOfferId, setSelectedOfferId] = useState<string | null>(
    availableOffers[0]?.id ?? null,
  )
  const [quantity, setQuantity] = useState(1)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (availableOffers.length === 0) {
    return <EmptyState title="Nenhuma oferta disponível para este produto." />
  }

  const selectedOffer = availableOffers.find((offer) => offer.id === selectedOfferId) ?? null

  function selectOffer(offer: Offer) {
    setSelectedOfferId(offer.id)
    setQuantity(1)
    setError(null)
  }

  function updateQuantity(value: number) {
    if (!selectedOffer) {
      return
    }
    const bounded = Math.min(Math.max(1, value), selectedOffer.stock)
    setQuantity(bounded)
  }

  async function handleBuy() {
    if (!selectedOffer) {
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      const order = await createOrder({
        items: [
          {
            offer_id: selectedOffer.id,
            quantity,
            expected_price: selectedOffer.price,
          },
        ],
      })
      onPurchased(order)
    } catch (err) {
      if (err instanceof ApiRequestError && err.code === 'checkout_rejected') {
        const body = err.details
        if (isCheckoutRejectedBody(body) && body.items.length > 0) {
          setError(checkoutRejectReasonLabel(body.items[0].reason))
        } else {
          setError(err.message)
        }
      } else {
        setError(errorMessage(err))
      }
    } finally {
      setSubmitting(false)
    }
  }

  const total = selectedOffer ? Number(selectedOffer.price) * quantity : 0

  return (
    <div className={styles.panel}>
      <ul className={styles.offerList}>
        {availableOffers.map((offer) => {
          const selected = selectedOfferId === offer.id
          return (
            <li key={offer.id}>
              <label
                className={`${styles.offerOption} ${selected ? styles.offerOptionSelected : ''}`.trim()}
              >
                <input
                  type="radio"
                  name="offer"
                  checked={selected}
                  onChange={() => selectOffer(offer)}
                />
                <span className={styles.offerSeller}>{offer.seller.name}</span>
                <span className={styles.offerPrice}>{formatCurrencyBRL(offer.price)}</span>
                <span className={styles.offerStock}>{offer.stock} em estoque</span>
              </label>
            </li>
          )
        })}
      </ul>

      {selectedOffer && (
        <div className={styles.form}>
          <TextField
            label="Quantidade"
            name="quantity"
            type="number"
            min={1}
            max={selectedOffer.stock}
            value={quantity}
            onChange={(event) => updateQuantity(Number(event.target.value))}
            fieldClassName={styles.quantity}
          />

          <div className={styles.total}>
            <span className={styles.totalLabel}>Total</span>
            <span className={styles.totalValue}>{formatCurrencyBRL(String(total))}</span>
          </div>

          {error && (
            <p className={styles.error} role="alert">
              {error}
            </p>
          )}

          <Button type="button" onClick={handleBuy} loading={submitting} fullWidth>
            Comprar
          </Button>
        </div>
      )}
    </div>
  )
}
