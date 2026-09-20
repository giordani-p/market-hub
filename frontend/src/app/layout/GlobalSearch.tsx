import { Search } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import type { UserRole } from '../../types/auth'
import { isCompleteUuid } from '../../lib/utils/useUrlFilters'
import { isPublicNumber } from '../../lib/utils/orderNumber'
import styles from './GlobalSearch.module.css'

/** Lista de pedidos de cada papel, destino da busca por ID ou numero. */
const ORDER_LIST_PATH: Record<UserRole, string | null> = {
  buyer: '/buyer/orders',
  seller: '/seller/orders',
  ops: '/ops/order-items',
}

const PLACEHOLDER: Record<UserRole, string> = {
  buyer: 'Buscar produto ou número do pedido',
  seller: 'Buscar produto ou número do pedido',
  ops: 'Buscar produto ou número do pedido',
}

/**
 * Busca do header.
 *
 * Nao ha endpoint de busca global no backend, entao ela despacha para a
 * tela que ja sabe filtrar: UUID vai para a lista com order_item_id;
 * numero publico vai com number; qualquer outro termo vai para o catalogo.
 */
export function GlobalSearch({ role }: { role: UserRole }) {
  const navigate = useNavigate()
  const [term, setTerm] = useState('')

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const value = term.trim()
    if (!value) {
      return
    }
    const orderListPath = ORDER_LIST_PATH[role]
    if (orderListPath && isCompleteUuid(value)) {
      if (role === 'buyer') {
        navigate(`/catalog?q=${encodeURIComponent(value)}`)
        return
      }
      navigate(`${orderListPath}?order_item_id=${value}`)
      return
    }
    if (orderListPath && isPublicNumber(value)) {
      navigate(`${orderListPath}?number=${encodeURIComponent(value)}`)
      return
    }
    navigate(`/catalog?q=${encodeURIComponent(value)}`)
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} role="search">
      <Search size={16} className={styles.icon} aria-hidden="true" />
      <label className="sr-only" htmlFor="global-search">
        Buscar
      </label>
      <input
        id="global-search"
        className={styles.input}
        type="search"
        value={term}
        onChange={(event) => setTerm(event.target.value)}
        placeholder={PLACEHOLDER[role]}
      />
    </form>
  )
}
